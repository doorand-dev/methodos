"""Local fixtures only: no browser, provider submission, or real Codex wake."""
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import web_review_wake as cli


THREAD = "1a111111-1111-4111-8111-111111111111"


class WebWakeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run = Path(temporary.name) / "run"
        self.run.mkdir()
        (self.run / "prompt.txt").write_text("검토 요청", encoding="utf-8")
        self.manifest = {
            "service": "chatgpt", "tab_id": "tab-1", "url": "https://chatgpt.com/c/fixture",
            "model_requested": "Pro", "account_selector": None,
            "prompt_sha256": hashlib.sha256("검토 요청".encode()).hexdigest(),
            "submissions_attempted": 1, "submission_confirmed": False,
            "status": "submission_uncertain", "output_obtained": False,
            "error": "click receipt lost",
        }
        self.persist()
        self.request = self.run / "approval.txt"
        self.request.write_text("최종 검토가 저장되면 이 채팅을 깨워줘.\n", encoding="utf-8")
        self.directory = self.run / "wake"
        self.args = argparse.Namespace(run=self.run, thread=THREAD, timeout=60,
                                       user_request_file=self.request)

    def persist(self):
        cli.write(self.run / "manifest.json", self.manifest)

    def prepare_worker(self):
        self.directory.mkdir()
        _, fixed = cli.binding(self.run)
        self.state = {"run": str(self.run.resolve()), "binding": fixed, "thread": THREAD,
                      "timeout": 60, "user_request": self.request.read_text(encoding="utf-8")}
        cli.save(self.directory, self.state, "starting")

    def complete(self):
        data = "최종 검토\n본문".encode()
        (self.run / "output.txt").write_bytes(data)
        self.manifest.update(status="completed", output_obtained=True, submission_confirmed=True,
                             output_sha256=hashlib.sha256(data).hexdigest())
        self.manifest.pop("error", None)
        self.persist()

    def status(self):
        return cli.read(self.directory / "state.json")["status"]

    def wake_receipt(self, action, thread, remaining, message=None):
        self.assertGreater(remaining, 0)
        self.assertTrue((self.directory / "final.json").is_file())
        if action == "probe":
            return 0, {"thread_id": thread, "execution_status": "idle"}
        self.assertEqual(self.status(), "wake_attempting")
        text = message.read_text(encoding="utf-8")
        self.assertIn(self.state["user_request"], text)
        self.assertIn(str(self.run / "output.txt"), text)
        self.assertIn(str(self.run / "manifest.json"), text)
        self.assertNotIn("최종 검토\n본문", text)
        return 0, {"thread_id": thread, "transport_status": "accepted"}

    def test_uncertain_send_recovers_only_by_poll_then_wakes_once(self):
        self.prepare_worker()

        def collect(run, remaining):
            wake.assert_not_called()
            self.complete()
            return 0, {"status": "completed"}

        with patch.object(cli, "poll", side_effect=collect) as poll, \
                patch.object(cli, "wake_command", side_effect=self.wake_receipt) as wake, \
                patch.object(cli.time, "sleep"):
            cli.watch(self.directory)
            with self.assertRaises(ValueError):
                cli.watch(self.directory)
        self.assertEqual(poll.call_count, 1)
        self.assertEqual([call.args[0] for call in wake.call_args_list], ["probe", "send"])
        self.assertEqual(self.status(), "wake_accepted")

    def test_completed_aistudio_uses_local_final_without_poll(self):
        self.manifest.update(service="aistudio", url="https://aistudio.google.com/prompts/new_chat",
                             model_requested="gemini-3.8-flash")
        self.complete()
        self.prepare_worker()
        with patch.object(cli, "poll") as poll, \
                patch.object(cli, "wake_command", side_effect=self.wake_receipt):
            cli.watch(self.directory)
        poll.assert_not_called()
        self.assertEqual(self.status(), "wake_accepted")

    def test_completed_hash_missing_output_multiple_submission_never_wake(self):
        self.complete()
        for changed in ({"output_sha256": "wrong"}, {"output_obtained": False},
                        {"submissions_attempted": 2}, {"submission_confirmed": False}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                cli.final_answer(self.run, {**self.manifest, **changed})
        (self.run / "output.txt").unlink()
        with self.assertRaises(ValueError):
            cli.final_answer(self.run, self.manifest)
        self.prepare_worker()
        with patch.object(cli, "poll") as poll, patch.object(cli, "wake_command") as wake:
            cli.watch(self.directory)
        poll.assert_not_called()
        wake.assert_not_called()
        self.assertEqual(self.status(), "collection_failed")

    def test_binding_and_prompt_changes_rejected(self):
        self.prepare_worker()
        for field, value in (("tab_id", "other"), ("service", "other"),
                             ("url", "https://chatgpt.com/c/other"),
                             ("prompt_sha256", "other"), ("model_requested", "other")):
            original = self.manifest[field]
            self.manifest[field] = value
            self.persist()
            with self.subTest(field=field), self.assertRaises(ValueError):
                cli.checked_run(self.state)
            self.manifest[field] = original
        self.persist()
        (self.run / "prompt.txt").write_text("변경", encoding="utf-8")
        with self.assertRaises(ValueError):
            cli.checked_run(self.state)

    def test_pending_and_slice_timeout_continue_but_terminal_block_stops(self):
        self.prepare_worker()
        statuses = iter(["pending", "timeout", "blocked_usage_limit"])

        def collect(run, remaining):
            self.manifest["status"] = next(statuses)
            self.persist()
            return 2, {"status": self.manifest["status"]}

        with patch.object(cli, "poll", side_effect=collect) as poll, \
                patch.object(cli, "wake_command") as wake, patch.object(cli.time, "sleep"):
            cli.watch(self.directory)
        self.assertEqual(poll.call_count, 3)
        wake.assert_not_called()
        self.assertEqual(self.status(), "collection_failed")

    def test_watch_budget_timeout_never_final(self):
        self.prepare_worker()
        with patch.object(cli.time, "monotonic", side_effect=[0, 61]), \
                patch.object(cli, "poll") as poll, patch.object(cli, "wake_command") as wake:
            cli.watch(self.directory)
        self.assertEqual(self.status(), "timed_out")
        poll.assert_not_called()
        wake.assert_not_called()
        self.assertFalse((self.directory / "final.json").exists())

    def test_lock_and_poll_errors_stop_without_wake(self):
        self.prepare_worker()
        with patch.object(cli, "poll", return_value=(2, {"error": "active lock exists"})) as poll, \
                patch.object(cli, "wake_command") as wake:
            cli.watch(self.directory)
        self.assertEqual(poll.call_count, 1)
        wake.assert_not_called()
        self.assertEqual(self.status(), "collection_failed")

    def test_uncertain_wake_is_never_retried_even_without_marker(self):
        self.complete()
        self.prepare_worker()

        def uncertain(action, *args):
            if action == "probe":
                return 0, {"thread_id": THREAD, "execution_status": "idle"}
            raise subprocess.TimeoutExpired("mock wake", 30)

        with patch.object(cli, "wake_command", side_effect=uncertain) as wake:
            cli.watch(self.directory)
            self.assertEqual(self.status(), "wake_uncertain")
            (self.directory / "worker.started").unlink()
            with self.assertRaises(ValueError):
                cli.watch(self.directory)
        self.assertEqual(wake.call_count, 2)

    def test_worker_marker_blocks_concurrent_worker(self):
        self.prepare_worker()
        (self.directory / "worker.started").write_text("other pid", encoding="ascii")
        with patch.object(cli, "poll") as poll, patch.object(cli, "wake_command") as wake:
            with self.assertRaises(FileExistsError):
                cli.watch(self.directory)
        self.assertEqual(self.status(), "starting")
        poll.assert_not_called()
        wake.assert_not_called()

    def test_start_validation_and_launch_failure(self):
        with patch.object(cli.subprocess, "Popen", side_effect=OSError("mock spawn failure")) as spawn:
            for value in (0, -1, float("nan"), float("inf")):
                self.args.timeout = value
                with self.assertRaises(ValueError):
                    cli.start(self.args)
            self.args.timeout = 60
            self.args.thread = "invalid"
            with self.assertRaises(ValueError):
                cli.start(self.args)
            self.args.thread = THREAD
            self.manifest["submissions_attempted"] = 0
            self.persist()
            with self.assertRaises(ValueError):
                cli.start(self.args)
            spawn.assert_not_called()
            self.manifest["submissions_attempted"] = 1
            self.persist()
            with self.assertRaises(OSError):
                cli.start(self.args)
            self.assertEqual(self.status(), "start_failed")
            with self.assertRaises(FileExistsError):
                cli.start(self.args)
            self.assertEqual(spawn.call_count, 1)

    def test_start_checks_completed_hash_and_os_before_launch(self):
        self.complete()
        (self.run / "output.txt").write_text("changed", encoding="utf-8")
        with patch.object(cli.subprocess, "Popen") as spawn:
            with self.assertRaises(ValueError):
                cli.start(self.args)
            with patch.object(cli.os, "name", "posix"), self.assertRaisesRegex(ValueError, "Windows"):
                cli.start(self.args)
        spawn.assert_not_called()
        self.assertFalse(self.directory.exists())

    def test_probe_unknown_never_sends(self):
        self.complete()
        self.prepare_worker()
        with patch.object(cli, "wake_command", return_value=(0, {
                "thread_id": THREAD, "execution_status": "unknown"})) as wake:
            cli.watch(self.directory)
        self.assertEqual(wake.call_count, 1)
        self.assertEqual(self.status(), "wake_probe_failed")
        self.assertTrue((self.directory / "final.json").exists())

    def test_start_success_keeps_all_state_in_run_and_uses_detached_worker(self):
        with patch.object(cli.subprocess, "Popen") as spawn:
            spawn.return_value.pid = 123
            result = cli.start(self.args)
        self.assertEqual(result, {"directory": str(self.directory.resolve()), "watcher_pid": 123})
        self.assertEqual(self.status(), "starting")
        command = spawn.call_args.args[0]
        self.assertEqual(command[-2:], ["_worker", str(self.directory.resolve())])
        self.assertTrue(spawn.call_args.kwargs["creationflags"] & subprocess.DETACHED_PROCESS)

    def test_status_is_local_and_shared_cli_arguments_are_collect_only(self):
        self.prepare_worker()
        with patch.object(cli.subprocess, "run") as run, patch.object(cli.subprocess, "Popen") as spawn, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(["status", str(self.directory)]), 0)
        run.assert_not_called()
        spawn.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["status"], "starting")
        with patch.object(cli, "json_command", return_value=(0, {})) as command:
            cli.poll(self.run, 4)
            args = command.call_args.args[0]
            self.assertEqual(args[4:], ["poll", str(self.run), "--timeout", "4"])
            cli.wake_command("send", THREAD, 5, self.directory / "wake.txt")
            args = command.call_args.args[0]
            self.assertIn(str(cli.CODEX_WAKE), args)
            self.assertEqual(args[4:11], ["send", "--thread", THREAD, "--caller", THREAD, "--timeout", "5"])


if __name__ == "__main__":
    unittest.main()
