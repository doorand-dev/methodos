"""Submit one AI Studio review in a detached REPL, collect its final, then wake.

The worker owns its temporary tab until collection ends. Existing web_generation
guards and web_review_wake delivery are reused; no API or retry submission exists.
"""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

import web_generation as generation
import web_review_wake as wake


def now():
    return datetime.now(timezone.utc).isoformat()


def event(directory, name, **values):
    with (directory / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"at": now(), "event": name, **values}, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def update(directory, state, status, **values):
    state.update(status=status, updated_at=now(), **values)
    wake.write(directory / "job.json", state)


class ReviewBrowser(generation.Aside):
    def __init__(self, account, directory):
        self.directory = directory
        self.submitted_at = None
        super().__init__(account)
        try:
            # A new review is explicitly requested. Never reuse an existing chat.
            self.target = self.call(
                'const before=new Set((await listBrowserTabs()).map(t=>t.targetId));'
                'const own=await openTab("https://aistudio.google.com/");'
                'await snapshot(own,{interactive:true});'
                'const added=(await listBrowserTabs()).filter(t=>!before.has(t.targetId)'
                '&&new URL(t.url).hostname==="aistudio.google.com");'
                'if(added.length!==1)throw Error("New review tab identity not found");'
                'return added[0].targetId;')
            event(directory, "tab_opened", target=self.target)
        except Exception:
            self.close()
            raise

    def invoke(self, method, *args):
        if method == "attach":
            args = (args[0], self.target)
        if method == "submit":
            self.submitted_at = time.monotonic()
            event(self.directory, "submission_call_started")
        result = super().invoke(method, *args)
        elapsed = round(time.monotonic() - self.submitted_at, 3) if self.submitted_at is not None else None
        if method == "submit":
            event(self.directory, "submission_call_returned", elapsed_seconds=elapsed)
        if method == "collect":
            event(self.directory, "observation", elapsed_seconds=elapsed,
                  has_output=bool(result.get("output")), complete=bool(result.get("complete")),
                  prompt_matches=bool(result.get("prompt_matches")))
        return result


def worker(directory):
    directory = directory.resolve()
    state = wake.read(directory / "job.json")
    # A crash or repeat invocation cannot submit twice, even before a manifest exists.
    with (directory / "worker.started").open("x", encoding="ascii") as marker:
        marker.write(str(os.getpid()))
        marker.flush()
        os.fsync(marker.fileno())
    try:
        update(directory, state, "probing")
        if generation.digest((directory / "prompt.txt").read_text(encoding="utf-8")) != state["prompt_sha256"]:
            raise ValueError("Saved review prompt has changed; nothing submitted")
        code, probe = wake.wake_command("probe", state["thread"], 30)
        if code or probe.get("thread_id") != state["thread"] or probe.get("execution_status") not in ("idle", "running"):
            raise RuntimeError("Wake target probe failed; nothing submitted")
        update(directory, state, "reviewing")
        event(directory, "review_started")
        command = ["--account", state["account"], "run", "aistudio",
                   "--model", state["model"], "--reasoning", state["reasoning"],
                   "--prompt", str(directory / "prompt.txt"), "--out", str(directory / "run"),
                   "--timeout", str(state["timeout"])]
        code = generation.main(command, browser_factory=lambda account: ReviewBrowser(account, directory))
        manifest = wake.read(directory / "run/manifest.json")
        if code or not wake.final_answer(directory / "run", manifest):
            update(directory, state, "review_failed", review_status=manifest.get("status"))
            return
        event(directory, "final_saved", output_sha256=manifest["output_sha256"])
        # The existing watcher revalidates the binding/hash, waits for the chat to
        # become idle and sends once. It never receives an intermediate answer.
        receipt = wake.start(argparse.Namespace(
            run=directory / "run", thread=state["thread"], timeout=state["wake_timeout"],
            user_request_file=directory / "user-request.txt"))
        update(directory, state, "wake_started", wake=receipt)
        event(directory, "wake_started", receipt=receipt)
    except Exception as exc:
        update(directory, state, "failed", error=str(exc))
        event(directory, "failed", error=str(exc))


def submit(args):
    if os.name != "nt":
        raise ValueError("Detached launcher currently supports Windows only")
    thread = wake.validate_options(args.thread, args.timeout)
    if not math.isfinite(args.wake_timeout) or args.wake_timeout <= 0:
        raise ValueError("--wake-timeout must be positive and finite")
    if not wake.CODEX_WAKE.is_file():
        raise ValueError("Install the shared Codex Wake CLI before submitting")
    if not generation.DRIVER.is_file():
        raise ValueError("Install the complete skill folder, including web_generation_browser.js")
    prompt = args.prompt.read_text(encoding="utf-8-sig")
    request = args.user_request_file.read_text(encoding="utf-8-sig")
    if not prompt.strip() or not request.strip():
        raise ValueError("Prompt and original user wake authorization are required")
    directory = args.out.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "prompt.txt").write_text(prompt, encoding="utf-8", newline="")
    (directory / "user-request.txt").write_text(request, encoding="utf-8", newline="")
    state = {"version": 1, "created_at": now(), "thread": thread, "account": args.account,
             "model": args.model, "reasoning": args.reasoning, "timeout": args.timeout,
             "wake_timeout": args.wake_timeout, "prompt_sha256": generation.digest(prompt)}
    update(directory, state, "starting")
    try:
        with (directory / "worker.log").open("ab") as log:
            child = subprocess.Popen(
                [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "_worker", str(directory)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)
    except OSError as exc:
        update(directory, state, "start_failed", error=str(exc))
        raise
    return {"directory": str(directory), "worker_pid": child.pid, "status": "starting"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    launch = sub.add_parser("submit", help="Send one authorized review, collect final, then wake")
    launch.add_argument("--account", required=True, help="Aside account:profile selector")
    launch.add_argument("--model", required=True, help="Exact AI Studio model id observed in the UI")
    launch.add_argument("--reasoning", default="Medium", help="Verify current AI Studio Thinking Level")
    launch.add_argument("--prompt", type=Path, required=True)
    launch.add_argument("--out", type=Path, required=True, help="New job directory; never reuse")
    launch.add_argument("--thread", required=True)
    launch.add_argument("--user-request-file", type=Path, required=True)
    launch.add_argument("--timeout", type=float, default=900)
    launch.add_argument("--wake-timeout", type=float, default=3600)
    for name in ("status", "_worker"):
        sub.add_parser(name).add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "_worker":
            worker(args.directory)
            return 0
        value = submit(args) if args.command == "submit" else wake.read(args.directory / "job.json")
        print(json.dumps(value, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
