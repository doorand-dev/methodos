"""Offline checks only: no real app, CLI queue, or thread is contacted."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import codex_wake as wake


TARGET = "11111111-1111-4111-8111-111111111111"
CALLER = "22222222-2222-4222-8222-222222222222"
MESSAGE_ID = "33333333-3333-4333-8333-333333333333"


def snapshot(status="idle"):
    return {"thread": {"id": TARGET, "status": {"type": status}}, "turns": []}


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.connect = patch.object(wake, "_connect", return_value=(self.client, snapshot(), "node"))
        self.connect.start()
        self.addCleanup(self.connect.stop)
        self.run = patch.object(wake.subprocess, "run")
        self.runner = self.run.start()
        self.addCleanup(self.run.stop)

    def send(self):
        return wake.send(TARGET, "한글 알림", caller_thread_id=CALLER, command=["node", "codex.js"])

    def running(self):
        wake._connect.return_value = (self.client, {
            "thread": {"id": TARGET}, "turns": [{"status": "inProgress"}]}, "node")

    def test_idle_app_receipt(self):
        self.client.call.return_value = {"threadId": TARGET}
        result = self.send()
        self.assertEqual((result["transport_status"], result["execution_status"]), ("accepted", "unconfirmed"))
        self.assertIsNone(result["message_id"])
        self.client.call.assert_called_once_with("send_message_to_thread", {"threadId": TARGET, "prompt": "한글 알림"})
        self.client.close.assert_called_once()
        self.runner.assert_not_called()

    def test_app_timeout_and_wrong_receipt_never_fallback(self):
        for result in (wake.BridgeError("timeout"), {"threadId": CALLER}):
            with self.subTest(result=result):
                self.client.call.side_effect = result if isinstance(result, Exception) else None
                self.client.call.return_value = result
                with self.assertRaises(wake.WakeUncertain):
                    self.send()
        self.runner.assert_not_called()

    def test_running_queues_once_and_sanitizes_environment(self):
        self.running()
        self.runner.return_value = subprocess.CompletedProcess([], 0, f"Queued message {MESSAGE_ID} for thread {TARGET}.\n", "")
        with patch.dict(os.environ, {"CODEX_THREAD_ID": CALLER, "CODEX_HOME": "home"}):
            result = self.send()
        self.assertEqual(result["transport_status"], "queued")
        self.assertEqual(result["execution_status"], "unconfirmed")
        self.client.call.assert_not_called()
        args, kwargs = self.runner.call_args
        self.assertEqual(args[0], ["node", "codex.js", "queue", "--thread", TARGET, "--message", "한글 알림"])
        self.assertNotIn("CODEX_THREAD_ID", kwargs["env"])
        self.assertEqual(kwargs["env"]["CODEX_HOME"], "home")

    def test_queue_timeout_and_unknown_receipt_are_uncertain(self):
        self.running()
        for response in (subprocess.TimeoutExpired("fake", 1), subprocess.CompletedProcess([], 0, "", ""),
                         subprocess.CompletedProcess([], 1, f"Queued message {MESSAGE_ID} for thread {TARGET}.", "")):
            with self.subTest(response=response):
                self.runner.side_effect = response if isinstance(response, Exception) else None
                self.runner.return_value = response
                with self.assertRaises(wake.WakeUncertain):
                    self.send()

    def test_unknown_state_does_not_send(self):
        wake._connect.return_value = (self.client, snapshot("unknown"), "node")
        with self.assertRaises(wake.WakeRejected):
            self.send()
        self.client.call.assert_not_called()
        self.runner.assert_not_called()

    def test_read_only_probe(self):
        result = wake.probe(TARGET, caller_thread_id=CALLER)
        self.assertEqual(result["execution_status"], "idle")
        self.client.call.assert_not_called()
        self.runner.assert_not_called()
        self.client.close.assert_called_once()

    def test_nonzero_queue_exit_without_receipt_is_uncertain(self):
        self.running()
        self.runner.return_value = subprocess.CompletedProcess([], 1, "", "failed")
        with self.assertRaises(wake.WakeUncertain):
            self.send()
        self.runner.assert_called_once()
        self.client.call.assert_not_called()

    def test_wrong_queue_target_is_uncertain_without_retry(self):
        self.running()
        self.runner.return_value = subprocess.CompletedProcess(
            [], 0, f"Queued message {MESSAGE_ID} for thread {CALLER}.", "")
        with self.assertRaises(wake.WakeUncertain):
            self.send()
        self.runner.assert_called_once()

    def test_queue_start_failure_is_rejected(self):
        self.running()
        self.runner.side_effect = FileNotFoundError("fake queue executable")
        with self.assertRaises(wake.WakeRejected):
            self.send()
        self.runner.assert_called_once()

    def test_invalid_input_never_connects(self):
        for target, caller, timeout, message in (
            ("invalid", CALLER, 1, "event"), (TARGET, "invalid", 1, "event"),
            (TARGET, CALLER, 0, "event"), (TARGET, CALLER, float("nan"), "event"),
            (TARGET, CALLER, float("inf"), "event"), (TARGET, CALLER, 1, " "),
        ):
            with self.subTest(target=target, caller=caller, timeout=timeout, message=message):
                with self.assertRaises(wake.WakeRejected):
                    wake.send(target, message, caller_thread_id=caller, timeout=timeout)
        wake._connect.assert_not_called()

    def test_unrecognized_turn_cannot_fall_back_to_idle(self):
        for turns in ([{"status": "new-status"}], [None], {"status": "inProgress"}):
            value = snapshot()
            value["turns"] = turns
            wake._connect.return_value = self.client, value, "node"
            with self.assertRaises(wake.WakeRejected):
                self.send()
        self.client.call.assert_not_called()
        self.runner.assert_not_called()

    def test_terminal_turns_are_idle(self):
        for status in ("completed", "interrupted", "failed"):
            self.assertFalse(wake._running({"turns": [{"status": status}]}))


class ConnectionTests(unittest.TestCase):
    def test_cli_uncertain_exit_is_distinct_from_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "message.txt"
            path.write_text("event", encoding="utf-8")
            for error, code, outcome in ((wake.WakeUncertain("unknown"), 2, "uncertain"),
                                          (wake.WakeRejected("invalid"), 1, "rejected")):
                with patch.object(wake, "send", side_effect=error), patch("builtins.print") as output:
                    actual = wake.main(["send", "--thread", TARGET, "--caller", CALLER,
                                        "--message-file", str(path)])
                self.assertEqual(actual, code)
                self.assertEqual(json.loads(output.call_args.args[0])["outcome"], outcome)

    def test_cli_explicit_path_overrides_config_and_probe_ignores_command(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text(json.dumps({"node_path": "from-file", "command": ["fake"]}), encoding="utf-8")
            with patch.object(wake, "probe", return_value={}) as probe, patch("builtins.print"):
                self.assertEqual(wake.main(["probe", "--thread", TARGET, "--caller", CALLER,
                                           "--config", str(config), "--node-path", "explicit"]), 0)
            probe.assert_called_once_with(TARGET, node_path="explicit", caller_thread_id=CALLER, timeout=30)

    def test_cli_rejects_unknown_config_keys_before_connect(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            config.write_text('{"unexpected": true}', encoding="utf-8")
            with patch.object(wake, "_connect") as connect, patch("builtins.print"):
                self.assertEqual(wake.main(["probe", "--thread", TARGET, "--caller", CALLER,
                                           "--config", str(config)]), 1)
            connect.assert_not_called()

    def test_login_without_session_env_finds_unique_bundled_node(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            node = root / "OpenAI/Codex/runtimes/cua_node/version/bin/node.exe"
            node.parent.mkdir(parents=True)
            node.touch()
            server = root / "server.mjs"
            server.touch()
            with patch.dict(os.environ, {"LOCALAPPDATA": directory, "CODEX_MCP_NODE_PATH": ""}), \
                    patch.object(wake.shutil, "which", return_value=None):
                actual_node, _ = wake._paths(server_path=str(server))
            self.assertEqual(actual_node, str(node.resolve()))

    def test_multiple_bundled_nodes_fail_but_explicit_or_env_wins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for version in ("one", "two"):
                node = root / f"OpenAI/Codex/runtimes/cua_node/{version}/bin/node.exe"
                node.parent.mkdir(parents=True)
                node.touch()
            server = root / "server.mjs"
            server.touch()
            explicit = root / "explicit-node.exe"
            explicit.touch()
            with patch.dict(os.environ, {"LOCALAPPDATA": directory, "CODEX_MCP_NODE_PATH": ""}), \
                    patch.object(wake.shutil, "which", return_value=None):
                with self.assertRaisesRegex(wake.WakeRejected, "node_path_ambiguous"):
                    wake._paths(server_path=str(server))
                self.assertEqual(wake._paths(str(explicit), str(server))[0], str(explicit.resolve()))
                with patch.dict(os.environ, {"CODEX_MCP_NODE_PATH": str(explicit)}):
                    self.assertEqual(wake._paths(server_path=str(server))[0], str(explicit.resolve()))

    def test_stale_env_rediscovers_only_endpoint(self):
        stale, fresh = Mock(), Mock()
        stale.initialize.side_effect = wake.BridgeError("pipe missing")
        fresh.call.return_value = snapshot()
        with patch.object(wake, "_paths", return_value=("node", "server")), \
                patch.object(wake, "Client", side_effect=[stale, fresh]) as factory, \
                patch.object(wake, "_pipe_candidates", return_value=["fresh"]), \
                patch.dict(os.environ, {"CODEX_APP_TOOLS_PIPE_PATH": "stale"}):
            client, value, _ = wake._connect(TARGET, CALLER, 1)
        self.assertIs(client, fresh)
        self.assertEqual(value, snapshot())
        stale.close.assert_called_once()
        self.assertEqual(factory.call_args_list[1].args[2], "fresh")
        fresh.call.assert_called_once_with("read_thread", {"threadId": TARGET, "turnLimit": 1,
                                          "includeOutputs": False, "maxOutputCharsPerItem": 0})

    def test_ambiguous_endpoints_fail_without_sending(self):
        with patch.object(wake, "_paths", return_value=("node", "server")), \
                patch.object(wake, "Client") as factory, \
                patch.object(wake, "_pipe_candidates", return_value=["one", "two"]), \
                patch.dict(os.environ, {"CODEX_APP_TOOLS_PIPE_PATH": ""}):
            with self.assertRaisesRegex(wake.WakeRejected, "ambiguous"):
                wake._connect(TARGET, CALLER, 1)
        factory.assert_not_called()

    def test_fake_mcp_stdio_metadata_and_child_cleanup(self):
        script = '''import json, sys
for line in sys.stdin:
    req = json.loads(line)
    if "id" not in req:
        continue
    result = {} if req["method"] == "initialize" else {"content": [{"type": "text", "text": json.dumps(req["params"])}]}
    print(json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": result}), flush=True)
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fake_mcp.py"
            path.write_text(script, encoding="utf-8")
            client = wake.Client(sys.executable, str(path), "fake", CALLER, 2)
            try:
                client.initialize()
                result = client.call("read_thread", {"threadId": TARGET})
                self.assertEqual(result["_meta"], {"openai/threadId": CALLER})
                self.assertEqual(result["arguments"], {"threadId": TARGET})
            finally:
                client.close()
            self.assertIsNotNone(client.process.poll())

    def test_cli_reads_utf8_message_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "message.txt"
            path.write_text("한글 알림", encoding="utf-8-sig")
            with patch.object(wake, "send", return_value={"transport_status": "accepted"}) as send, \
                    patch("builtins.print"):
                code = wake.main(["send", "--thread", TARGET, "--caller", CALLER, "--message-file", str(path)])
            self.assertEqual(code, 0)
            send.assert_called_once_with(TARGET, "한글 알림", caller_thread_id=CALLER, timeout=30)

    def test_cli_probe_omits_snapshot(self):
        result = {"thread_id": TARGET, "execution_status": "running", "snapshot": {"private": "turn content"}}
        with patch.object(wake, "probe", return_value=result), patch("builtins.print") as output:
            code = wake.main(["probe", "--thread", TARGET, "--caller", CALLER])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.call_args.args[0]), {"thread_id": TARGET, "execution_status": "running"})


if __name__ == "__main__":
    unittest.main()
