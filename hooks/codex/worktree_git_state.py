#!/usr/bin/env python3
"""worktree_git_state.py -- 메인(공유) 체크아웃의 git 상태 스냅샷.

worktree-advisory.py(SessionStart 주입)가 사용한다. 새 state(lock/heartbeat)를
만들지 않고 git이 *이미 기록한* 흔적만 읽는다:
  - 현재 브랜치 + 마지막 HEAD 이동 시각(reflog, --date=relative)
  - working tree dirty 파일 목록(status --porcelain) = "지금 누가 편집 중"
  - 최근 커밋 시각/제목

level:
  - "warn"   : dirty>0  또는  (비-기본 브랜치 & 전환이 최근=분/초 단위)
               -> 동시/최근 활동 신호. 격리 권고.
  - "info"   : 비-기본 브랜치인데 전환이 오래됨 -> 잔여물 가능성.
  - "silent" : main/master & clean -> 주입 안 함(솔로 마찰 0).
"""
import os
import re
import subprocess

DEFAULT_BRANCHES = {"main", "master"}
_RECENT_UNITS = ("second", "minute")  # 분/초 = 동시성 신호


def _run_git(cwd: str, *args: str):
    try:
        out = subprocess.run(
            ["git", "-C", cwd, *args],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def in_primary_checkout(cwd: str):
    """True=1차 체크아웃 / False=워크트리 / None=판별불가."""
    gd = _run_git(cwd, "rev-parse", "--git-dir")
    cd = _run_git(cwd, "rev-parse", "--git-common-dir")
    if gd is None or cd is None:
        return None

    def resolve(p: str) -> str:
        p = p.strip()
        if not os.path.isabs(p):
            p = os.path.join(cwd, p)
        return os.path.normcase(os.path.realpath(p))

    return resolve(gd) == resolve(cd)


def _reflog_last(cwd: str):
    """(상대시각, 액션). 예: ('2 minutes ago', 'checkout: moving from main to x')."""
    out = _run_git(cwd, "reflog", "--date=relative", "--format=%gd%x09%gs", "-1")
    if not out:
        return (None, None)
    lines = out.splitlines()
    if not lines or "\t" not in lines[0]:
        return (None, None)
    gd, gs = lines[0].split("\t", 1)
    m = re.search(r"\{([^}]*)\}", gd)
    return (m.group(1) if m else None, gs.strip())


def _is_recent(rel) -> bool:
    return bool(rel) and any(u in rel for u in _RECENT_UNITS)


def snapshot(cwd: str) -> dict:
    branch = _run_git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    branch = branch.strip() if branch else None
    switch_rel, switch_action = _reflog_last(cwd)
    status = _run_git(cwd, "status", "--porcelain")
    dirty = [ln for ln in (status.splitlines() if status else []) if ln.strip()]
    last = _run_git(cwd, "log", "-1", "--format=%cr%x09%s")
    lc_rel, lc_subj = (None, None)
    if last:
        lines = last.splitlines()
        if lines and "\t" in lines[0]:
            lc_rel, lc_subj = lines[0].split("\t", 1)

    snap = {
        "branch": branch,
        "switch_rel": switch_rel,
        "switch_action": switch_action,
        "dirty": dirty,
        "dirty_count": len(dirty),
        "last_commit_rel": lc_rel,
        "last_commit_subject": lc_subj,
    }
    snap["level"] = _level(snap)
    return snap


def _level(snap: dict) -> str:
    b = snap["branch"]
    nondefault = bool(b) and b not in DEFAULT_BRANCHES and b != "HEAD"
    if snap["dirty_count"] > 0 or (nondefault and _is_recent(snap["switch_rel"])):
        return "warn"
    if nondefault:
        return "info"
    return "silent"


def _dirty_path(line: str) -> str:
    """porcelain 한 줄(' M path')에서 경로만."""
    return line[3:].strip() if len(line) > 3 else line.strip()


def format_advisory(snap: dict) -> str:
    """SessionStart additionalContext용 블록. silent면 ''."""
    if snap["level"] == "silent":
        return ""
    sw = f" ({snap['switch_rel']} 전환)" if snap["switch_rel"] else ""
    lines = [
        "[worktree-advisory] 메인(공유) 체크아웃 상태:",
        f"  브랜치: {snap['branch']}{sw}",
    ]
    if snap["dirty_count"]:
        lines.append(
            f"  ⚠️ uncommitted {snap['dirty_count']}개 — 다른 세션이 편집 중일 수 있음:"
        )
        for ln in snap["dirty"][:10]:
            lines.append(f"     {ln}")
        if snap["dirty_count"] > 10:
            lines.append(f"     … 외 {snap['dirty_count'] - 10}개")
    if snap["last_commit_rel"]:
        lines.append(
            f"  최근 커밋: {snap['last_commit_rel']} \"{snap['last_commit_subject']}\""
        )
    if snap["level"] == "warn":
        lines.append(
            "  → foreign dirty/staged/untracked를 보존하고 exact owned path의"
        )
        lines.append(
            "    겹침을 먼저 확인하라. 격리가 필요하면 "
            "~/.codex/rules/worktree.md를 읽어라."
        )
    else:  # info
        lines.append(
            "  → 비-기본 브랜치 잔여물 가능성. 브랜치를 전환하지 말고 현재"
        )
        lines.append("    작업의 ownership을 확인한 뒤 worktree 규칙을 적용하라.")
    return "\n".join(lines)


def format_inline(snap: dict) -> str:
    """B 차단 메시지용 짧은 한 줄. 신호 없으면 ''."""
    if not snap or not snap.get("branch"):
        return ""
    parts = [f"현재 {snap['branch']}"]
    if snap["switch_rel"]:
        parts.append(f"{snap['switch_rel']} 전환")
    if snap["dirty_count"]:
        sample = ", ".join(
            os.path.basename(_dirty_path(d)) for d in snap["dirty"][:3]
        )
        more = " …" if snap["dirty_count"] > 3 else ""
        parts.append(f"{snap['dirty_count']} dirty: {sample}{more}")
    return "(" + ", ".join(parts) + ")"
