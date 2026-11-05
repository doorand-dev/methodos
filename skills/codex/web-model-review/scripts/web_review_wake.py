"""Collect an already submitted web_generation run, then wake one authorized chat.

No submission path is exposed. A durable worker marker deliberately requires
manual investigation after a crash; uncertain wake receipts are never retried.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import UUID


WEBGEN = Path(__file__).with_name("web_generation.py")
CODEX_WAKE = Path(os.environ.get("CODEX_WAKE_PATH") or
                  (Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "tools/codex_wake.py"))
SLICE_SECONDS = 30
RECHECK_SECONDS = 3
PENDING = {"waiting", "pending", "timeout", "submission_uncertain"}


def read(path):
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def write(path, value):
    # The exclusive directory/worker marker ensures a single writer.
    with path.with_suffix(".tmp").open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    path.with_suffix(".tmp").replace(path)


def save(directory, state, status, **evidence):
    state.update(status=status, **evidence)
    write(directory / "state.json", state)


def validate_options(thread, timeout):
    thread = str(UUID(thread))
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("--timeout must be positive and finite")
    return thread


def binding(run):
    manifest = read(run / "manifest.json")
    attempts = manifest.get("submissions_attempted")
    if type(attempts) is not int or attempts < 1:
        raise ValueError("Run must already have attempted submission")
    if manifest.get("service") not in ("chatgpt", "aistudio"):
        raise ValueError("Only chatgpt/aistudio runs are supported")
    if not isinstance(manifest.get("tab_id"), str) or not manifest["tab_id"].strip():
        raise ValueError("Run must bind an existing tab identity")
    prompt = (run / "prompt.txt").read_text(encoding="utf-8")
    if not prompt.strip() or hashlib.sha256(prompt.encode("utf-8")).hexdigest() != manifest.get("prompt_sha256"):
        raise ValueError("Saved prompt SHA does not match")
    fixed = {key: manifest.get(key) for key in
             ("service", "tab_id", "prompt_sha256", "model_requested", "account_selector")}
    # A blank/temporary tab may acquire a conversation URL during recovery.
    chat = re.match(r"^https://chatgpt\.com/c/[^/?#]+", manifest.get("url") or "")
    fixed["conversation"] = chat[0] if chat else None
    return manifest, fixed


def checked_run(state):
    run = Path(state["run"])
    manifest, fixed = binding(run)
    expected = state["binding"]
    for key in expected:
        if key != "conversation" and fixed[key] != expected[key]:
            raise ValueError(f"Run binding changed: {key}")
    if expected["conversation"] and fixed["conversation"] != expected["conversation"]:
        raise ValueError("Run conversation changed")
    return manifest


def final_answer(run, manifest):
    if manifest.get("status") != "completed":
        return False
    output = run / "output.txt"
    if (manifest.get("output_obtained") is not True
            or type(manifest.get("submissions_attempted")) is not int
            or manifest["submissions_attempted"] != 1
            or manifest.get("submission_confirmed") is not True
            or not output.is_file()):
        raise ValueError("Completed run lacks verified single-submission output")
    data = output.read_bytes()
    if not data.strip() or hashlib.sha256(data).hexdigest() != manifest.get("output_sha256"):
        raise ValueError("Saved output SHA does not match")
    return True


def json_command(command, timeout):
    result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        value = json.loads(result.stdout)
        if not isinstance(value, dict):
            raise ValueError("Expected object")
    except ValueError as exc:
        raise RuntimeError(f"Command returned invalid JSON (exit {result.returncode})") from exc
    return result.returncode, value


def poll(run, remaining):
    seconds = min(SLICE_SECONDS, remaining)
    return json_command([sys.executable, "-X", "utf8", str(WEBGEN), "poll", str(run),
                         "--timeout", str(seconds)], timeout=seconds + 10)


def wake_command(action, thread, remaining, message=None):
    seconds = min(30, remaining)
    command = [sys.executable, "-X", "utf8", str(CODEX_WAKE), action,
               "--thread", thread, "--caller", thread, "--timeout", str(seconds)]
    if message is not None:
        command += ["--message-file", str(message)]
    return json_command(command, timeout=seconds + 10)


def watch(directory):
    directory = directory.resolve()
    state = read(directory / "state.json")
    validate_options(state["thread"], state["timeout"])
    if directory != Path(state["run"]).resolve() / "wake":
        raise ValueError("Watcher must live in its run/wake directory")
    if state["status"] != "starting":
        raise ValueError("Watcher already ran; inspect existing state, do not retry")
    with (directory / "worker.started").open("x", encoding="ascii") as marker:
        marker.write(str(os.getpid()))
        marker.flush()
        os.fsync(marker.fileno())
    deadline = time.monotonic() + state["timeout"]
    phase = "collect"
    run = Path(state["run"])
    try:
        save(directory, state, "watching")
        while True:
            manifest = checked_run(state)
            if final_answer(run, manifest):
                write(directory / "final.json", {"output": str(run / "output.txt"),
                      "manifest": str(run / "manifest.json"), "output_sha256": manifest["output_sha256"]})
                save(directory, state, "final_saved")
                break
            if manifest.get("status") not in PENDING:
                raise RuntimeError(f"Collection stopped: {manifest.get('status')}; {manifest.get('error', '')}")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                save(directory, state, "timed_out")
                return
            code, receipt = poll(run, remaining)
            if code not in (0, 2) or receipt.get("error"):
                raise RuntimeError(f"Poll failed: {receipt.get('error') or code}")
            # Always inspect the durable manifest, not just the poll receipt.
            if receipt.get("status") in PENDING and time.monotonic() < deadline:
                time.sleep(min(RECHECK_SECONDS, max(0, deadline - time.monotonic())))

        phase = "probe"
        while (remaining := deadline - time.monotonic()) > 0:
            code, receipt = wake_command("probe", state["thread"], remaining)
            if code or receipt.get("thread_id") != state["thread"]:
                raise RuntimeError("Codex Wake probe failed")
            if receipt.get("execution_status") == "idle":
                break
            if receipt.get("execution_status") != "running":
                raise RuntimeError("Codex chat status is unknown")
            time.sleep(min(RECHECK_SECONDS, max(0, deadline - time.monotonic())))
        else:
            save(directory, state, "final_saved_chat_busy")
            return
        # Revalidate immediately before sending; no browser access is needed.
        if not final_answer(run, checked_run(state)):
            raise ValueError("Final changed")
        message = directory / "wake.txt"
        message.write_text(
            "[Web 검토 watcher→원래 Codex 채팅 · 에이전트 간 전달]\n"
            f"원래 채팅 사용자 승인 원문: “{state['user_request']}”\n"
            f"최종 검토를 저장했습니다. {run / 'output.txt'}\n"
            f"검증 기록: {run / 'manifest.json'}\n", encoding="utf-8")
        if deadline - time.monotonic() <= 0:
            save(directory, state, "final_saved_chat_busy")
            return
        save(directory, state, "wake_attempting")
        phase = "wake"
        code, receipt = wake_command("send", state["thread"], deadline - time.monotonic(), message)
        if code == 0 and receipt.get("thread_id") == state["thread"] and receipt.get("transport_status") in ("accepted", "queued"):
            status = "wake_" + receipt["transport_status"]
        else:
            status = "wake_rejected" if receipt.get("outcome") == "rejected" else "wake_uncertain"
        save(directory, state, status, wake_receipt=receipt)
    except Exception as exc:
        save(directory, state, {"collect": "collection_failed", "probe": "wake_probe_failed",
                               "wake": "wake_uncertain"}[phase], error=str(exc))


def start(args):
    if os.name != "nt":
        raise ValueError("Detached watcher launcher supports Windows only")
    thread = validate_options(args.thread, args.timeout)
    if not WEBGEN.is_file() or not CODEX_WAKE.is_file():
        raise ValueError("web_generation and shared Codex Wake CLI are required")
    run = args.run.resolve()
    manifest, fixed = binding(run)
    final_answer(run, manifest)  # Completed runs must pass hashes even at launch.
    if manifest.get("status") != "completed" and manifest.get("status") not in PENDING:
        raise ValueError("Run is blocked or failed; inspect it before watching")
    user_request = args.user_request_file.read_text(encoding="utf-8-sig")
    if not user_request.strip():
        raise ValueError("Provide the original user request explicitly authorizing wake")
    directory = run / "wake"
    directory.mkdir(exist_ok=False)
    state = {"run": str(run), "binding": fixed, "thread": thread,
             "timeout": args.timeout, "user_request": user_request}
    save(directory, state, "starting")
    try:
        with (directory / "worker.log").open("ab") as log:
            child = subprocess.Popen(
                [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "_worker", str(directory)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    except OSError as exc:
        save(directory, state, "start_failed", error=str(exc))
        raise
    return {"directory": str(directory), "watcher_pid": child.pid}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    launch = sub.add_parser("start")
    launch.add_argument("--run", type=Path, required=True)
    launch.add_argument("--thread", required=True)
    launch.add_argument("--user-request-file", type=Path, required=True)
    launch.add_argument("--timeout", type=float, default=3600)
    for name in ("status", "_worker"):
        sub.add_parser(name).add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "_worker":
            watch(args.directory)
        else:
            result = start(args) if args.command == "start" else read(args.directory / "state.json")
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
