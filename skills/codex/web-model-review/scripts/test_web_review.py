"""Detached review boundary tests; no browser, external submission or wake."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import web_review as cli


THREAD = "1a111111-1111-4111-8111-111111111111"


class ReviewTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.job = Path(temporary.name) / "job"
        self.job.mkdir()
        (self.job / "prompt.txt").write_text("검토", encoding="utf-8")
        (self.job / "user-request.txt").write_text("최종 답변에서 여기 깨워줘", encoding="utf-8")
        self.state = {"thread": THREAD, "account": "fixture", "model": "fixture-model",
                      "reasoning": "Medium", "timeout": 60, "wake_timeout": 60,
                      "prompt_sha256": cli.generation.digest("검토")}
        cli.update(self.job, self.state, "starting")

    def complete(self, command, **kwargs):
        self.assertIn("browser_factory", kwargs)
        self.assertIn("run", command)
        self.assertNotIn("send", command)
        self.notify.assert_not_called()
        cli.event(self.job, "observation", has_output=True, complete=False)
        self.notify.assert_not_called()
        run = self.job / "run"
        state = cli.generation.new_run(run, self.state.get("service", "aistudio"), "fixture-model", "검토", self.job / "prompt.txt", "fixture")
        (run / "output.txt").write_text("최종", encoding="utf-8", newline="")
        state.update(status="completed", output_obtained=True, submission_confirmed=True,
                     submissions_attempted=1, output_sha256=cli.generation.digest("최종"), tab_id="fixture-tab")
        cli.generation.save(run, state)
        return 0

    def run_worker(self, generate=None, probe=None):
        with patch.object(cli.wake, "wake_command", return_value=probe or (0, {"thread_id": THREAD, "execution_status": "running"})), \
                patch.object(cli.generation, "main", side_effect=generate or self.complete) as generate_mock, \
                patch.object(cli.wake, "start", return_value={"directory": "fixture", "watcher_pid": 1}) as notify:
            self.notify = notify
            cli.worker(self.job)
        return generate_mock, notify

    def test_only_verified_final_starts_wake(self):
        generate, notify = self.run_worker()
        self.assertEqual(generate.call_count, 1)
        self.assertEqual(notify.call_count, 1)
        self.assertEqual(cli.wake.read(self.job / "job.json")["status"], "wake_started")
        events = (self.job / "events.jsonl").read_text(encoding="utf-8")
        self.assertLess(events.index('"event": "final_saved"'), events.index('"event": "wake_started"'))

    def test_worker_cannot_submit_twice(self):
        self.run_worker()
        with patch.object(cli.generation, "main") as generate, self.assertRaises(FileExistsError):
            cli.worker(self.job)
        generate.assert_not_called()

    def test_chatgpt_uses_same_final_wake_path_and_exact_reasoning(self):
        self.state.update(service="chatgpt", reasoning="Pro")
        cli.update(self.job, self.state, "starting")
        generate, notify = self.run_worker()
        command = generate.call_args.args[0]
        self.assertEqual(command[command.index("run") + 1], "chatgpt")
        self.assertEqual(command[command.index("--reasoning") + 1], "Pro")
        notify.assert_called_once()

    def test_legacy_jobs_still_route_to_aistudio(self):
        generate, _ = self.run_worker()
        command = generate.call_args.args[0]
        self.assertEqual(command[command.index("run") + 1], "aistudio")

    def test_owned_tab_cannot_attach_to_another_service(self):
        browser = cli.ReviewBrowser.__new__(cli.ReviewBrowser)
        browser.review_service = "chatgpt"
        browser.target = "fixture"
        with patch.object(cli.generation.Aside, "invoke") as invoke:
            with self.assertRaisesRegex(ValueError, "service differs"):
                browser.invoke("attach", "aistudio", None)
        invoke.assert_not_called()

    def test_changed_prompt_never_submits(self):
        (self.job / "prompt.txt").write_text("다른 내용", encoding="utf-8")
        generate, notify = self.run_worker()
        generate.assert_not_called()
        notify.assert_not_called()

    def test_probe_failure_never_submits(self):
        generate, notify = self.run_worker(probe=(2, {"error": "offline"}))
        generate.assert_not_called()
        notify.assert_not_called()

    def test_uncertain_collection_reuses_owned_browser_and_polls_without_resend(self):
        browser = Mock()
        with patch.object(cli, "ReviewBrowser") as factory:
            factory.return_value = browser
            calls = []
            def recover(command, **kwargs):
                self.assertFalse(kwargs["close_browser"])
                self.assertIs(kwargs["browser_factory"]("fixture"), browser)
                calls.append(command)
                run = self.job / "run"
                if len(calls) == 1:
                    run.mkdir()
                    cli.wake.write(run / "manifest.json", {"status": "submission_uncertain", "submissions_attempted": 1})
                    return 2
                self.assertEqual(command[0], "poll")
                self.assertNotIn("send", command)
                self.assertNotIn("run", command)
                state = cli.wake.read(run / "manifest.json")
                (run / "output.txt").write_text("최종", encoding="utf-8", newline="")
                state.update(status="completed", submissions_attempted=1, submission_confirmed=True,
                             output_obtained=True, output_sha256=cli.generation.digest("최종"), tab_id="fixture")
                cli.generation.save(run, state)
                return 0
            with patch.object(cli.time, "sleep"):
                generate, notify = self.run_worker(generate=recover)
            self.assertEqual(generate.call_count, 2)
            self.assertEqual(factory.call_count, 1)
            browser.close.assert_called_once()
            notify.assert_called_once()

    def test_intermediate_or_timeout_never_wakes(self):
        def timeout(command, **kwargs):
            run = self.job / "run"
            run.mkdir()
            cli.wake.write(run / "manifest.json", {"status": "timeout"})
            return 2
        _, notify = self.run_worker(generate=timeout)
        notify.assert_not_called()
        self.assertEqual(cli.wake.read(self.job / "job.json")["status"], "review_failed")

    def test_changed_final_never_wakes(self):
        def corrupt(command, **kwargs):
            self.complete(command, **kwargs)
            (self.job / "run/output.txt").write_text("바뀜", encoding="utf-8")
            return 0
        _, notify = self.run_worker(generate=corrupt)
        notify.assert_not_called()
        self.assertEqual(cli.wake.read(self.job / "job.json")["status"], "failed")


if __name__ == "__main__":
    unittest.main()
