"""Unofficial Windows helper to wake an authorized existing Codex thread.

Only Python's standard library is required. ``probe`` is read-only; ``send`` reads
the target first, uses app MCP for idle threads and ``codex queue`` for running
threads. A receipt confirms acceptance only, never execution. WakeUncertain means
delivery may already have happened: inspect it instead of retrying automatically.

Paths can be passed as keyword arguments (or a CLI --config JSON object containing
node_path, server_path, pipe_path, command). No credentials are read or saved.
Only the MCP child created by this module is closed; the app stays running.
"""

import argparse
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid


class WakeRejected(RuntimeError):
    """No delivery was attempted (including failure to start the queue process)."""

    outcome_known = True


class WakeUncertain(RuntimeError):
    """Delivery may have happened; no automatic retry or fallback is safe."""

    outcome_known = False


class BridgeError(RuntimeError):
    pass


def _flags():
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _validate(thread_id, caller_thread_id, timeout):
    for label, value in (("thread", thread_id), ("caller", caller_thread_id)):
        try:
            uuid.UUID(value)
        except (ValueError, TypeError, AttributeError) as exc:
            raise WakeRejected(f"{label}_uuid_required") from exc
    if not isinstance(timeout, (float, int)) or not math.isfinite(timeout) or timeout <= 0:
        raise WakeRejected("positive_finite_timeout_required")


def _unique_path(paths, label):
    existing = {str(Path(path).resolve()) for path in paths if path and Path(path).is_file()}
    if len(existing) != 1:
        raise WakeRejected(f"{label}_{'ambiguous' if existing else 'unavailable'}; pass an explicit path")
    return existing.pop()


def _resources():
    """Inspect installation paths only, never user databases or credentials."""
    roots = []
    tectonic = os.environ.get("CODEX_TECTONIC_PATH")
    if tectonic:
        roots.extend(parent for parent in Path(tectonic).parents if parent.name == "resources")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "Programs" / "Codex" / "resources")
    programs = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
    try:
        roots.extend((programs / "WindowsApps").glob("OpenAI.Codex_*/app/resources"))
    except OSError:
        pass
    # Windows PowerShell exposes Appx even when the caller uses PowerShell 7.
    if not any(root.is_dir() for root in roots) and os.name == "nt":
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 "Get-AppxPackage -Name OpenAI.Codex | Select-Object -ExpandProperty InstallLocation"],
                capture_output=True, text=True, timeout=10, creationflags=_flags(), shell=False)
            if result.returncode == 0:
                roots.extend(Path(line.strip()) / "app" / "resources"
                             for line in result.stdout.splitlines() if line.strip())
        except (OSError, subprocess.TimeoutExpired):
            pass
    return roots


def _paths(node_path=None, server_path=None):
    node = node_path or os.environ.get("CODEX_MCP_NODE_PATH") or shutil.which("node")
    if node:
        node = _unique_path([node], "node_path")
    else:
        # A Windows login Startup process does not inherit a Codex session's
        # CODEX_MCP_NODE_PATH or its PATH additions. Use the installed runtime.
        local = os.environ.get("LOCALAPPDATA")
        runtime = (Path(local) if local else Path.home() / "AppData/Local") / "OpenAI/Codex/runtimes/cua_node"
        try:
            candidates = list(runtime.glob("*/bin/node.exe"))
        except OSError:
            candidates = []
        node = _unique_path(candidates, "node_path")
    server = server_path or os.environ.get("CODEX_APP_TOOLS_SERVER_PATH")
    candidates = [server] if server else [
        root / "plugins/openai-bundled/plugins/codex-app-tools/server.mjs" for root in _resources()]
    return node, _unique_path(candidates, "server_path")


def _command(node_path, command=None):
    if command is not None:
        if (not isinstance(command, list) or not command or
                any(not isinstance(item, str) or not item.strip() for item in command)):
            raise WakeRejected("command_must_be_nonempty_string_list")
        return command
    # Invoke JS directly; Windows .ps1 launchers cannot be Popen executables.
    candidates = []
    launcher = shutil.which("codex")
    if launcher:
        candidates.append(Path(launcher).parent / "node_modules/@openai/codex/bin/codex.js")
    roaming = os.environ.get("APPDATA")
    if roaming:
        candidates.append(Path(roaming) / "npm/node_modules/@openai/codex/bin/codex.js")
    existing = [path for path in candidates if path.is_file()]
    if existing:
        return [node_path, _unique_path(existing, "codex_cli")]
    runtime = os.environ.get("CODEX_APP_RUNTIME_CLI_PATH")
    if runtime and Path(runtime).is_file():
        return [runtime]
    raise WakeRejected("codex_cli_unavailable; pass command=[node_path, codex_js_path]")


class Client:
    """JSON-lines client for a version-dependent bundled app stdio bridge.

    This adapter is not an official or stable Codex API.
    """

    def __init__(self, node_path, server_path, pipe_path, caller_thread_id, timeout):
        self.timeout = timeout
        self.caller_thread_id = caller_thread_id
        self.responses = queue.Queue()
        self.next_id = 0
        self.process = subprocess.Popen(
            [node_path, server_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
            env=dict(os.environ, CODEX_APP_TOOLS_PIPE_PATH=pipe_path),
            creationflags=_flags(), shell=False)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            for line in self.process.stdout:
                self.responses.put(json.loads(line))
        except (OSError, ValueError) as exc:
            self.responses.put(BridgeError(f"mcp_invalid_response: {exc}"))
        finally:
            self.responses.put(BridgeError("mcp_closed"))

    def _write(self, value):
        self.process.stdin.write(json.dumps(value, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.next_id += 1
        request_id = self.next_id
        self._write({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                response = self.responses.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise BridgeError("mcp_timed_out") from exc
            if isinstance(response, Exception):
                raise response
            if not isinstance(response, dict):
                raise BridgeError("mcp_object_required")
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise BridgeError("mcp_error: " + str(response["error"]))
            if "result" not in response:
                raise BridgeError("mcp_result_missing")
            return response["result"]

    def initialize(self):
        self.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                     "clientInfo": {"name": "codex-wake", "version": "1"}})
        self._write({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def call(self, name, arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments,
                              "_meta": {"openai/threadId": self.caller_thread_id}})
        if not isinstance(result, dict) or result.get("isError"):
            raise BridgeError("app_tool_rejected_or_invalid")
        texts = [item.get("text") for item in result.get("content", [])
                 if isinstance(item, dict) and item.get("type") == "text"]
        try:
            value = json.loads(texts[0]) if len(texts) == 1 else None
        except (TypeError, ValueError) as exc:
            raise BridgeError("app_tool_json_unconfirmed") from exc
        if not isinstance(value, dict):
            raise BridgeError("app_tool_object_required")
        return value

    def close(self):
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        self.process.stdout.close()
        self.reader.join(timeout=1)


def _pipe_candidates():
    if os.name != "nt":
        return []
    try:
        return ["\\\\.\\pipe\\" + name for name in os.listdir("\\\\.\\pipe\\")
                if name.startswith("codex-app-tools-")]
    except OSError as exc:
        raise WakeRejected("app_pipe_enumeration_failed") from exc


def _connect(thread_id, caller_thread_id, timeout, node_path=None, server_path=None, pipe_path=None):
    node, server = _paths(node_path, server_path)
    attempted = set()

    def open_pipe(path):
        client = Client(node, server, path, caller_thread_id, timeout)
        try:
            client.initialize()
            snapshot = client.call("read_thread", {"threadId": thread_id, "turnLimit": 1,
                                   "includeOutputs": False, "maxOutputCharsPerItem": 0})
            target = snapshot.get("thread")
            if not isinstance(target, dict) or target.get("id") != thread_id:
                raise BridgeError("read_target_unconfirmed")
            return client, snapshot, node
        except Exception:
            client.close()
            raise

    for path in (pipe_path, os.environ.get("CODEX_APP_TOOLS_PIPE_PATH")):
        if not path or path in attempted:
            continue
        attempted.add(path)
        try:
            return open_pipe(path)
        except (BridgeError, OSError):
            pass  # Read-only attempts may rediscover a pipe after app restart.
    candidates = [path for path in _pipe_candidates() if path not in attempted]
    if len(candidates) != 1:
        raise WakeRejected("app_pipe_ambiguous" if candidates else "app_pipe_unavailable")
    try:
        return open_pipe(candidates[0])
    except (BridgeError, OSError) as exc:
        raise WakeRejected(f"app_connection_unavailable: {exc}") from exc


def _running(snapshot):
    turns = snapshot.get("turns") or []
    if turns:
        if not isinstance(turns, list) or not isinstance(turns[0], dict):
            raise WakeRejected("execution_status_unconfirmed; no delivery attempted")
        status = turns[0].get("status")
        if status == "inProgress":
            return True
        if status in {"completed", "interrupted", "failed"}:
            return False
        raise WakeRejected("execution_status_unconfirmed; no delivery attempted")
    target = snapshot.get("thread") or {}
    status = target.get("status") if isinstance(target, dict) else None
    if isinstance(status, dict) and status.get("type") == "idle":
        return False
    raise WakeRejected("execution_status_unconfirmed; no delivery attempted")


def probe(thread_id, *, caller_thread_id, timeout=30, node_path=None, server_path=None, pipe_path=None):
    """Read one small target snapshot and return confirmed idle/running status."""
    _validate(thread_id, caller_thread_id, timeout)
    client, snapshot, _ = _connect(thread_id, caller_thread_id, timeout, node_path, server_path, pipe_path)
    try:
        return {"thread_id": thread_id, "execution_status": "running" if _running(snapshot) else "idle",
                "snapshot": snapshot}
    finally:
        client.close()


def send(thread_id, message, *, caller_thread_id, timeout=30, node_path=None,
         server_path=None, pipe_path=None, command=None):
    """Deliver once. caller_thread_id supplies the authorized MCP caller context.

    command overrides the queue executable prefix, e.g. [node, codex_js]. Paths
    otherwise come from current app environment and installed paths. A successful
    dict has transport_status=accepted/queued and execution_status=unconfirmed.
    """
    _validate(thread_id, caller_thread_id, timeout)
    if not isinstance(message, str) or not message.strip():
        raise WakeRejected("message_required")
    client, snapshot, node = _connect(thread_id, caller_thread_id, timeout, node_path, server_path, pipe_path)
    try:
        if not _running(snapshot):
            try:
                result = client.call("send_message_to_thread", {"threadId": thread_id, "prompt": message})
                if result.get("threadId") != thread_id:
                    raise BridgeError("send_receipt_target_unconfirmed")
                return {"thread_id": thread_id, "message_id": result.get("messageId") or result.get("message_id"),
                        "transport_status": "accepted", "execution_status": "unconfirmed"}
            except Exception as exc:
                raise WakeUncertain(f"app_send_unconfirmed; inspect before retry: {exc}") from exc
    finally:
        client.close()
    prefix = _command(node, command)
    try:
        completed = subprocess.run(
            [*prefix, "queue", "--thread", thread_id, "--message", message],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, creationflags=_flags(), shell=False,
            env={key: value for key, value in os.environ.items()
                 if not key.startswith("CODEX_") or key == "CODEX_HOME"})
    except subprocess.TimeoutExpired as exc:
        raise WakeUncertain("queue_timed_out; inspect before retry") from exc
    except OSError as exc:
        raise WakeRejected(f"queue_process_unavailable: {exc}") from exc
    match = re.search(r"^Queued message ([0-9a-f-]{36}) for thread ([0-9a-f-]{36})\.$",
                      completed.stdout or "", re.MULTILINE)
    if completed.returncode != 0:
        if match:
            raise WakeUncertain("queue_receipt_with_failed_exit; inspect before retry")
        # An exit code alone cannot prove that the queue had no side effects.
        raise WakeUncertain(f"queue_failed_exit({completed.returncode}); inspect before retry")
    if not match or match[2] != thread_id:
        raise WakeUncertain("queue_receipt_unconfirmed; inspect before retry")
    return {"thread_id": thread_id, "message_id": match[1], "transport_status": "queued",
            "execution_status": "unconfirmed"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["probe", "send"])
    parser.add_argument("--thread", required=True)
    parser.add_argument("--caller", required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--config", help="JSON file with optional node_path/server_path/pipe_path/command")
    parser.add_argument("--node-path")
    parser.add_argument("--server-path")
    parser.add_argument("--pipe-path")
    parser.add_argument("--message-file", help="UTF-8 message file, required for send")
    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8-sig")) if args.config else {}
        if not isinstance(config, dict) or set(config) - {"node_path", "server_path", "pipe_path", "command"}:
            raise WakeRejected("config_keys_invalid")
        for name in ("node_path", "server_path", "pipe_path"):
            if getattr(args, name) is not None:
                config[name] = getattr(args, name)
        config.update(caller_thread_id=args.caller, timeout=args.timeout)
        if args.action == "probe":
            config.pop("command", None)
            result = probe(args.thread, **config)
            result = {key: value for key, value in result.items() if key != "snapshot"}
        else:
            if not args.message_file:
                raise WakeRejected("message_file_required")
            message = Path(args.message_file).read_text(encoding="utf-8-sig")
            result = send(args.thread, message, **config)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except WakeUncertain as exc:
        print(json.dumps({"error": str(exc), "outcome": "uncertain", "execution_status": "unconfirmed"}))
        return 2
    except (WakeRejected, BridgeError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "outcome": "rejected"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
