"""No browser/network: exercise submission and recovery boundaries."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

import web_generation as cli


class FakeAside:
    def __init__(self, account=None):
        self.session_dir = "fixture"
        self.calls = []
        self.prepare = {}
        self.fail_submit = False
        self.panel_result = {}
        self.tab = uuid.uuid4().hex

    def invoke(self, method, *args):
        self.calls.append(method)
        if method == "attach":
            return {"tab_id": self.tab, "url": "https://chatgpt.com/?temporary-chat=true"}
        if method == "prepare":
            return dict(self.prepare)
        if method == "closeInstructions":
            return {}
        if method == "readyAfterInstructions":
            return self.panel_result
        if method == "inspect":
            return {"model": "GPT-5.6 Sol"}
        if method == "fill":
            return {"editor_text": args[0], "input_matches": True}
        if method == "submit":
            if self.fail_submit:
                raise TimeoutError("click receipt lost")
            return {"clicked": True}
        if method == "collect":
            return {"prompt_matches": True, "output": "첫 출력", "complete": True,
                    "extraction": "fixture", "url": "https://chatgpt.com/c/fixture"}
        raise AssertionError(method)

    def close(self):
        pass


class GenerationSafetyTests(unittest.TestCase):
    def test_missing_driver_never_starts_a_browser_process(self):
        with patch.object(cli, "DRIVER", Path("missing-fixture/web_generation_browser.js")), \
                patch.object(cli.subprocess, "Popen") as spawn:
            with self.assertRaisesRegex(RuntimeError, "Missing browser driver"):
                cli.Aside()
        spawn.assert_not_called()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.prompt = self.root / "input.txt"
        self.prompt.write_text("한국어 프롬프트\n1. 사실", encoding="utf-8")
        self.out = self.root / "run"
        self.browser = FakeAside()

    def run_cli(self, args):
        with patch.object(cli, "Aside", return_value=self.browser), patch.object(cli.time, "sleep"), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return cli.main(args)

    def start(self, command="run"):
        return self.run_cli([command, "chatgpt", "--model", "GPT-5.6 Sol",
                             "--prompt", str(self.prompt), "--out", str(self.out)])

    def state(self):
        return json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))

    def test_configure_uses_the_pre_send_checks_without_filling_or_sending(self):
        args = ["configure", "chatgpt", "--tab", self.browser.tab, "--model", "GPT-6", "--reasoning", "High"]
        self.assertEqual(self.run_cli(args), 0)
        self.browser.prepare = {"blocked": "blocked_usage_limit"}
        self.assertEqual(self.run_cli([*args[:-1], "Pro"]), 2)
        self.assertEqual(self.browser.calls, ["attach", "prepare", "attach", "prepare"])

    def test_large_source_arguments_are_encoded_once_and_reused_on_poll(self):
        browser = cli.Aside.__new__(cli.Aside)
        browser._argument_cache = {}
        prompt = '코드 자료\nconst marker = "WEBGEN_";\n' * 2000
        with patch.object(browser, "call", return_value={}) as call:
            browser.invoke("collect", prompt)
            uploaded = call.call_count
            browser.invoke("collect", prompt)
            self.assertEqual(call.call_count, uploaded + 1)
            self.assertEqual(call.call_args_list[-1], call.call_args_list[-2])
            self.assertTrue(all(len(c.args[0]) < cli.RPC_CHUNK_CHARS + 256 for c in call.call_args_list))
            self.assertFalse(any(prompt in c.args[0] for c in call.call_args_list))

    def test_small_arguments_are_encoded_and_method_names_are_validated(self):
        browser = cli.Aside.__new__(cli.Aside)
        browser._argument_cache = {}
        with patch.object(browser, "call", return_value={}) as call:
            browser.invoke("inspect")
            self.assertIn("JSON.parse(Buffer.from(", call.call_args.args[0])
            with self.assertRaises(ValueError):
                browser.invoke("inspect;send")
            self.assertEqual(call.call_count, 1)

    def test_success_is_one_submit_and_second_run_cannot_overwrite(self):
        self.assertEqual(self.start(), 0)
        self.assertEqual(self.browser.calls.count("submit"), 1)
        before = (self.out / "manifest.json").read_bytes()
        self.assertEqual(self.start(), 2)
        self.assertEqual((self.out / "manifest.json").read_bytes(), before)
        self.assertEqual(self.browser.calls.count("submit"), 1)

    def test_instruction_dialog_is_closed_and_confirmed_before_any_fill(self):
        self.browser.prepare = {"close_system_instruction_panel": True, "system_instruction": ""}
        self.assertEqual(self.start("send"), 0)
        self.assertLess(self.browser.calls.index("closeInstructions"), self.browser.calls.index("readyAfterInstructions"))
        self.assertLess(self.browser.calls.index("readyAfterInstructions"), self.browser.calls.index("fill"))

    def test_instruction_dialog_failure_stops_before_fill_or_submission(self):
        self.browser.prepare = {"close_system_instruction_panel": True}
        self.browser.panel_result = {"blocked": "blocked_system_instruction_panel"}
        self.assertEqual(self.start(), 2)
        self.assertNotIn("fill", self.browser.calls)
        self.assertNotIn("submit", self.browser.calls)

    def test_lost_receipt_is_durable_and_resume_never_submits(self):
        self.browser.fail_submit = True
        self.assertEqual(self.start(), 2)
        self.assertEqual(self.state()["status"], "submission_uncertain")
        self.assertEqual(self.state()["submissions_attempted"], 1)
        self.assertEqual(self.run_cli(["resume", str(self.out)]), 0)
        self.assertEqual(self.browser.calls.count("submit"), 1)
        self.assertEqual(self.state()["recovered_errors"], ["click receipt lost"])

    def test_send_returns_before_collecting_output_and_poll_uses_saved_run(self):
        self.assertEqual(self.start("send"), 0)
        self.assertEqual(self.state()["status"], "waiting")
        self.assertTrue(self.state()["submission_confirmed"])
        self.assertFalse((self.out / "output.txt").exists())
        self.assertEqual(self.browser.calls.count("collect"), 1)
        with patch.object(cli, "Aside", side_effect=AssertionError("status must be local")) as aside, \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(cli.main(["status", str(self.out)]), 0)
        aside.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue())["status"], "waiting")
        self.assertEqual(self.run_cli(["poll", str(self.out)]), 0)
        self.assertEqual(self.browser.calls.count("submit"), 1)
        self.assertEqual((self.out / "output.txt").read_text(encoding="utf-8"), "첫 출력")

    def test_poll_rejects_same_prompt_in_a_different_chat(self):
        self.assertEqual(self.start("send"), 0)
        with patch.object(self.browser, "invoke", side_effect=lambda method, *args: {
            "attach": {"tab_id": self.browser.tab, "url": "https://chatgpt.com/c/other"},
            "collect": {"prompt_matches": True, "output": "wrong chat", "complete": True,
                        "url": "https://chatgpt.com/c/other"},
        }[method]):
            self.assertEqual(self.run_cli(["poll", str(self.out)]), 2)
        self.assertEqual(self.state()["status"], "blocked_conversation_changed")
        self.assertEqual(self.state()["url"], "https://chatgpt.com/c/fixture")
        self.assertFalse((self.out / "output.txt").exists())

    def test_access_and_mismatch_blocks_never_fill_or_submit(self):
        for reason in ("blocked_paid_access", "blocked_model_unavailable", "blocked_existing_conversation"):
            with self.subTest(reason=reason):
                self.out = self.root / reason
                self.browser.prepare = {"blocked": reason}
                self.assertEqual(self.start(), 2)
                self.assertEqual(self.state()["submissions_attempted"], 0)
                self.assertNotIn("fill", self.browser.calls)
                self.assertNotIn("submit", self.browser.calls)

    def test_resume_rejects_changed_input_and_completed_output(self):
        self.browser.fail_submit = True
        self.start()
        (self.out / "prompt.txt").write_text("changed", encoding="utf-8")
        previous = len(self.browser.calls)
        self.assertEqual(self.run_cli(["resume", str(self.out)]), 2)
        self.assertEqual(len(self.browser.calls), previous)
        self.out = self.root / "second"
        self.browser.fail_submit = False
        self.start()
        (self.out / "output.txt").write_text("changed", encoding="utf-8")
        self.assertEqual(self.run_cli(["resume", str(self.out)]), 2)

    def test_completed_text_without_matching_input_is_not_success(self):
        state = cli.new_run(self.out, "chatgpt", "exact", "prompt", self.prompt, None)
        with patch.object(self.browser, "invoke", return_value={
            "complete": True, "prompt_matches": False, "output": "another chat", "extraction": "fixture"
        }):
            cli.collect(self.browser, self.out, state, "prompt", timeout=0.02, poll_interval=0.01)
        self.assertEqual(state["status"], "submission_uncertain")
        self.assertFalse((self.out / "output.txt").exists())

    def test_stable_text_without_completion_signal_is_not_success(self):
        state = cli.new_run(self.out, "chatgpt", "exact", "prompt", self.prompt, None)
        with patch.object(self.browser, "invoke", return_value={
            "complete": False, "prompt_matches": True, "output": "still streaming", "extraction": "fixture"
        }):
            cli.collect(self.browser, self.out, state, "prompt", timeout=0.02, poll_interval=0.01)
        self.assertEqual(state["status"], "timeout")
        self.assertFalse((self.out / "output.txt").exists())

    def test_changed_model_after_response_is_not_success(self):
        state = cli.new_run(self.out, "chatgpt", "requested model", "prompt", self.prompt, None)
        cli.collect(self.browser, self.out, state, "prompt", timeout=1, poll_interval=0)
        self.assertEqual(state["status"], "blocked_model_changed")
        self.assertFalse((self.out / "output.txt").exists())

    def test_tab_lock_prevents_second_output_directory_from_submitting(self):
        root = Path(tempfile.gettempdir()) / "aside-web-generation"
        root.mkdir(exist_ok=True)
        lock = root / (cli.digest(self.browser.tab) + ".lock")
        lock.write_text("owned by another run", encoding="utf-8")
        self.addCleanup(lock.unlink)
        self.assertEqual(self.start(), 2)
        self.assertEqual(lock.read_text(encoding="utf-8"), "owned by another run")
        self.assertNotIn("prepare", self.browser.calls)
        self.assertNotIn("submit", self.browser.calls)


if __name__ == "__main__":
    unittest.main()
