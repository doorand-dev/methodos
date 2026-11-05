"""Generate text through the user's Aside tabs; never uses provider APIs.

Inspect first, then run or send with the exact UI model name/id and a UTF-8 prompt file.
One run directory is one submission. Poll and resume only collect.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid


DRIVER = Path(__file__).with_name("web_generation_browser.js")
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
RPC_CHUNK_CHARS = 16_000


class Aside:
    """Line framed RPC over documented `aside repl` stdin, without a shell."""

    def __init__(self, account=None):
        self._argument_cache = {}
        if not DRIVER.is_file():
            raise RuntimeError(f"Missing browser driver: {DRIVER}; install the complete skill folder")
        source = base64.b64encode(DRIVER.read_bytes()).decode("ascii")
        executable = shutil.which("aside")
        if not executable:
            raise RuntimeError("Aside CLI not installed")
        command = [executable, "repl"]
        if account:
            command += ["--account", account]
        self.process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1,
        )
        self.lines = queue.Queue()
        self.session_dir = None
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.call(f"eval(Buffer.from('{source}','base64').toString('utf8')); return true;")
        except Exception:
            self.close()
            raise

    def _read(self):
        for line in self.process.stdout:
            line = ANSI.sub("", line).strip()
            if line.startswith("sessionDir: "):
                self.session_dir = line.removeprefix("sessionDir: ")
            self.lines.put(line)
        self.lines.put(None)

    def call(self, code, timeout=125):
        marker = "WEBGEN_" + uuid.uuid4().hex + ":"
        # Entire payload travels through stdin, never through shell interpolation.
        wrapped = (
            "console.log(" + json.dumps(marker) + ",JSON.stringify(await (async()=>{"
            "try{return {ok:true,value:await (async()=>{" + code + "})()};}"
            "catch(e){return {ok:false,error:String(e)}}})()));\n"
        )
        self.process.stdin.write(wrapped)
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Aside REPL response timed out; action may have occurred")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("Aside REPL response timed out; action may have occurred") from exc
            if line is None:
                raise RuntimeError("Aside REPL exited before returning an action result")
            if marker in line:
                payload = json.loads(line.split(marker, 1)[1].strip())
                if not payload["ok"]:
                    raise RuntimeError(payload["error"])
                return payload.get("value")

    def invoke(self, method, *args):
        # Source code inside a literal REPL argument can confuse the CLI input
        # framing even when an equally long plain string succeeds. Encode the
        # data separately from JavaScript and cache large immutable arguments so
        # every poll does not retransmit the whole review packet.
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", method):
            raise ValueError("Invalid browser method")
        encoded = base64.b64encode(json.dumps(args, ensure_ascii=False).encode("utf-8")).decode("ascii")
        if len(encoded) <= RPC_CHUNK_CHARS:
            expression = f"JSON.parse(Buffer.from('{encoded}','base64').toString('utf8'))"
        else:
            key = "_webgen_args_" + hashlib.sha256(encoded.encode("ascii")).hexdigest()
            if key not in self._argument_cache:
                self.call(f"globalThis.{key}=''; return true;")
                for pos in range(0, len(encoded), RPC_CHUNK_CHARS):
                    self.call(f"globalThis.{key}+='{encoded[pos:pos + RPC_CHUNK_CHARS]}'; return true;")
                self.call(f"globalThis.{key}=JSON.parse(Buffer.from(globalThis.{key},'base64').toString('utf8')); return true;")
                self._argument_cache[key] = True
            expression = f"globalThis.{key}"
        return self.call(f"return await webgen.{method}(...{expression});")

    def close(self):
        if self.process.poll() is None:
            try:
                self.process.stdin.write("exit\n")
                self.process.stdin.flush()
                self.process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.process.terminate()


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def prepare(browser, model, reasoning, personalization, prompt):
    info = browser.invoke("prepare", model, reasoning, personalization, prompt)
    if info.pop("close_system_instruction_panel", False):
        browser.invoke("closeInstructions")
        closed = browser.invoke("readyAfterInstructions")
        if closed.get("blocked"):
            return {**info, **closed}
    return info


def save(directory, state):
    state["updated_at"] = timestamp()
    target = directory / "manifest.json"
    temporary = directory / "manifest.tmp"
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def receipt(directory, state):
    return {"status": state["status"], "manifest": str(directory / "manifest.json"),
            "tab_id": state.get("tab_id"), "url": state.get("url"),
            "submissions_attempted": state["submissions_attempted"],
            "submission_confirmed": state["submission_confirmed"],
            "output_obtained": state["output_obtained"]}


def new_run(directory, service, model, prompt, prompt_path, account):
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "prompt.txt").write_text(prompt, encoding="utf-8", newline="")
    return {
        "version": 1, "created_at": timestamp(), "status": "created",
        "service": service, "model_requested": model, "account_selector": account,
        "prompt_source": str(prompt_path.resolve()), "prompt_sha256": digest(prompt),
        "submissions_attempted": 0, "submission_confirmed": False,
        "runtime": "Aside repl; DOM UI only", "output_obtained": False,
        "driver_sha256": hashlib.sha256(DRIVER.read_bytes()).hexdigest(),
    }


def observe(browser, state, prompt):
    result = browser.invoke("collect", prompt)
    state["last_observation"] = {k: v for k, v in result.items() if k != "output"}
    # A ChatGPT tab can be reused for a different conversation between CLI calls.
    previous = state.get("url") or ""
    current = result.get("url") or ""
    saved_chat = re.match(r"^https://chatgpt\.com/c/[^/?#]+", previous)
    if saved_chat and not re.match(re.escape(saved_chat[0]) + r"(?:[/?#]|$)", current):
        state["status"] = "blocked_conversation_changed"
        return {**result, "blocked": state["status"]}
    state["submission_confirmed"] = state["submission_confirmed"] or result.get("prompt_matches", False)
    if current and result.get("prompt_matches"):
        state["url"] = current
    state["status"] = result.get("blocked") or (
        "waiting" if state["submission_confirmed"] else "submission_uncertain")
    return result


def collect(browser, directory, state, prompt, timeout, poll_interval):
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        result = observe(browser, state, prompt)
        if result.get("blocked"):
            state["status"] = result["blocked"]
            break
        output = result.get("output")
        # Both an explicit UI completion control and stable final text are required.
        if output and result.get("complete") and result.get("prompt_matches"):
            if output == previous:
                observed = browser.invoke("inspect")
                state["settings_after"] = observed
                if state["model_requested"] not in (observed.get("model"), observed.get("model_id")):
                    state["status"] = "blocked_model_changed"
                    break
                (directory / "output.txt").write_text(output, encoding="utf-8", newline="")
                state.update(status="completed", output_obtained=True,
                             output_sha256=digest(output), characters=len(output),
                             extraction=result["extraction"])
                if state.get("error"):
                    state.setdefault("recovered_errors", []).append(state.pop("error"))
                break
            previous = output
        else:
            previous = None
        save(directory, state)
        time.sleep(min(poll_interval, max(0, deadline - time.monotonic())))
    else:
        state["status"] = "timeout" if state["submission_confirmed"] else "submission_uncertain"
    save(directory, state)


def parser():
    p = argparse.ArgumentParser(description=__doc__, epilog=(
        "Open a blank temporary chat first. ChatGPT: configure applies model and reasoning without sending; "
        "run/send apply the same settings before sending. AI Studio: select the model and thinking level in the UI. "
        "send submits once and prints a receipt without waiting for completion; "
        "status reads the saved receipt without opening the browser. "
        "Exit 0: success; 2: blocked/uncertain/error. "
        "If interrupted, poll the same directory."
    ))
    p.add_argument("--account", help="Aside account/profile selector; otherwise current default")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("inspect", "run", "send"):
        cmd = sub.add_parser(name)
        cmd.add_argument("service", choices=("chatgpt", "aistudio"))
        cmd.add_argument("--tab", help="Exact existing tab targetId; required if multiple matching tabs")
        if name in ("run", "send"):
            cmd.add_argument("--model", required=True, help="Exact observed display name or AI Studio model id; no alias fallback")
            cmd.add_argument("--prompt", required=True, type=Path, help="UTF-8 text read locally; no attachment upload")
            cmd.add_argument("--out", required=True, type=Path, help="New run directory; never overwrite an existing run")
            cmd.add_argument("--reasoning", default="Medium", help="ChatGPT: set the displayed effort; AI Studio: verify it")
            cmd.add_argument("--personalization", choices=("off", "keep"), default="off",
                             help="ChatGPT: change only the current chat preference; keep records observed state")
            if name == "run":
                cmd.add_argument("--timeout", type=float, default=180)
    configure = sub.add_parser("configure", help="Set and verify ChatGPT model and reasoning; never type or send a prompt")
    configure.add_argument("service", choices=("chatgpt",))
    configure.add_argument("--tab", required=True, help="Exact targetId of an empty temporary ChatGPT tab")
    configure.add_argument("--model", required=True, help="Exact ChatGPT model name shown by inspect")
    configure.add_argument("--reasoning", required=True, help="Exact ChatGPT reasoning label")
    poll = sub.add_parser("poll", aliases=["resume"], help="Collect an existing run; never send or regenerate")
    poll.add_argument("directory", type=Path)
    poll.add_argument("--timeout", type=float, default=180)
    status = sub.add_parser("status", help="Show the saved run state without opening Aside")
    status.add_argument("directory", type=Path)
    return p


def main(argv=None, *, browser_factory=None):
    args = parser().parse_args(argv)
    if not math.isfinite(getattr(args, "timeout", 1)) or getattr(args, "timeout", 1) <= 0:
        raise SystemExit("--timeout must be positive")
    browser = None
    directory = None
    state = None
    lock_fd = None
    tab_lock = None
    tab_fd = None
    submitting = args.command in ("run", "send")
    collecting = args.command in ("poll", "resume")
    try:
        if submitting:
            prompt = args.prompt.read_text(encoding="utf-8-sig")
            if not prompt.strip():
                raise ValueError("Empty prompt")
            directory = args.out.resolve()
            state = new_run(directory, args.service, args.model, prompt, args.prompt, args.account)
            save(directory, state)
        elif collecting or args.command == "status":
            directory = args.directory.resolve()
            state = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
            if args.command == "status":
                print(json.dumps(receipt(directory, state), ensure_ascii=False))
                return 0
            if state["status"] == "completed":
                if digest((directory / "output.txt").read_text(encoding="utf-8")) != state["output_sha256"]:
                    raise ValueError("Saved output has changed; refusing completed status")
                print(json.dumps(receipt(directory, state), ensure_ascii=False))
                return 0
            if not state["submissions_attempted"]:
                raise ValueError("This run never attempted submission; resume cannot submit")
            prompt = (directory / "prompt.txt").read_text(encoding="utf-8")
            if digest(prompt) != state["prompt_sha256"]:
                raise ValueError("Saved prompt has changed")
        if directory:
            lock_fd = os.open(directory / ".active.lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        browser = (browser_factory or Aside)(state["account_selector"] if collecting else args.account)
        attached = browser.invoke("attach", state["service"] if collecting else args.service,
                                  state["tab_id"] if collecting else args.tab)
        # Protect the tab across different output directories and CLI processes.
        # A crash leaves a visible lock; never break another process's lock.
        lock_root = Path(tempfile.gettempdir()) / "aside-web-generation"
        lock_root.mkdir(exist_ok=True)
        tab_lock = lock_root / (digest(attached["tab_id"]) + ".lock")
        tab_fd = os.open(tab_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(tab_fd, json.dumps({"pid": os.getpid(), "run": str(directory)}).encode())
        if args.command == "inspect":
            info = attached
            info.update(browser.invoke("inspect"))
            print(json.dumps(info, ensure_ascii=False, indent=2))
            return 0
        if args.command == "configure":
            info = prepare(browser, args.model, args.reasoning, "keep", "")
            print(json.dumps({**attached, **info}, ensure_ascii=False, indent=2))
            return 2 if info.get("blocked") else 0
        if submitting:
            state.update(attached)
            save(directory, state)
            prepared = prepare(browser, args.model, args.reasoning, args.personalization, prompt)
            state["settings"] = prepared
            state["aside_session_directory"] = browser.session_dir
            if prepared.get("blocked"):
                state["status"] = prepared["blocked"]
            else:
                state["status"] = "prepared"
                save(directory, state)
                filled = browser.invoke("fill", prompt)
                editor_text = filled.pop("editor_text")
                (directory / "editor.txt").write_text(editor_text, encoding="utf-8", newline="")
                state["input_verification"] = filled
                # Write the intent BEFORE clicking. Failure after here is never auto-retried.
                state["status"] = "submission_uncertain"
                state["submissions_attempted"] = 1
                save(directory, state)
                browser.invoke("submit", prompt)
                if args.command == "send":
                    observe(browser, state, prompt)
                else:
                    collect(browser, directory, state, prompt, args.timeout, 3)
        else:
            collect(browser, directory, state, prompt, args.timeout, 3)
        save(directory, state)
        print(json.dumps(receipt(directory, state), ensure_ascii=False))
        success = state["status"] == "completed" or (args.command == "send" and state["status"] == "waiting")
        return 0 if success else 2
    except Exception as exc:
        if state is not None and lock_fd is not None:
            state["error"] = str(exc)
            state["status"] = "submission_uncertain" if state["submissions_attempted"] else "blocked_ui"
            save(directory, state)
        print(json.dumps({"error": str(exc), "manifest": str(directory / "manifest.json") if directory else None}, ensure_ascii=False), file=sys.stderr)
        return 2
    finally:
        if browser:
            browser.close()
        if tab_fd is not None:
            os.close(tab_fd)
            tab_lock.unlink()
        if lock_fd is not None:
            os.close(lock_fd)
            (directory / ".active.lock").unlink()


if __name__ == "__main__":
    raise SystemExit(main())
