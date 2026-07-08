"""GC 체크 — 프로젝트 내 불필요 파일/패턴 탐지 및 안전 정리.

Skill-local GC scripts. 본 레포 의존 0 — 어느 워크스페이스에서든 동작.

2등급 분리:
- safe-fix: __pycache__, .pyc, *.tmp, .DS_Store 등 → 무조건 삭제 OK
- review-fix: 끝난 .plans 후보, stale handoff 등 → 탐지만, 자동 삭제 금지

프로젝트별 보완: <workspace>/.claude/gc.toml 있으면 읽어서 skip_dirs/work_temp_dir 등 추가.

실행 모드:
- --safe-fix: safe 항목 자동 삭제
- --dry-run: 전체 스캔 보고 (safe + review)
- --review-only: review 카테고리만 체크 (/gc 스킬 §1 수동 호출용 — 자동 Stop 훅 없음)
- --report-json: JSON 출력
- --detect-large-dirs: top-level 큰 폴더 후보 보고 (SKILL.md 첫 실행 유도용)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import tomllib
except ImportError:
    tomllib = None

SAFE_DIR_NAMES = {"__pycache__"}
SAFE_FILE_SUFFIXES = {".pyc", ".pyo", ".tmp"}
SAFE_FILE_NAMES = {".DS_Store", "Thumbs.db"}
DEFAULT_SKIP_DIRS = {".git", "node_modules", ".venv", "venv"}

# .plans 정리 — 끝난 플랜 후보 판정
PLANS_DIR_NAME = ".plans"
PLANS_AGE_THRESHOLD_DAYS = 30
VERIFIED_PASS_RE = re.compile(r"<!--\s*VERIFIED:\s*PASS\b")
DOD_UNCHECKED_RE = re.compile(r"^- \[ \]", re.MULTILINE)
DOD_CHECKED_RE = re.compile(r"^- \[[xX]\]", re.MULTILINE)

# handoff 정리 — 1회용·휘발성. 새 세션 부트스트랩 후 stale.
HANDOFF_DIR = Path(".claude_context") / "handoff"
HANDOFF_AGE_THRESHOLD_DAYS = 14

# todo-ctx 정리 (관련 설계 결정) — 사이드카는 age-out 아니라 연결 todo 종결/소멸 기준.
TODOS_PATH = Path(".claude") / "todos.md"
TODO_CTX_DIR = Path(".claude") / "todo-ctx"
TODO_OPEN_RE = re.compile(r"^\s*-\s*\[\s\]\s*`?#(\d{3})\b", re.MULTILINE)
TODO_CLOSED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s*`?#(\d{3})\b", re.MULTILINE)
TODO_CTX_FILE_RE = re.compile(r"^(\d{3})\.json$")

# 큰 폴더 감지 임계 (SKILL.md 첫 실행 유도)
LARGE_DIR_THRESHOLD_MB = 100


def _find_project_root() -> Path:
    """현재 작업 디렉토리에서 위로 .git 디렉토리를 찾는다.

    못 찾으면 cwd 반환 (단일 폴더 작업 등 git 아닌 환경 대비).
    """
    p = Path.cwd()
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    return Path.cwd()


def _load_gc_toml(root: Path) -> dict:
    """<root>/.claude/gc.toml 로드. 없거나 파싱 실패 시 빈 dict."""
    toml_path = root / ".claude" / "gc.toml"
    if not toml_path.is_file() or tomllib is None:
        return {}
    try:
        with toml_path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _resolved_skip_dirs(toml_cfg: dict) -> set[str]:
    """기본 SKIP_DIRS + toml 의 skip_dirs 머지."""
    extra = set(toml_cfg.get("skip_dirs", []))
    return DEFAULT_SKIP_DIRS | extra


def _scan_safe(root: Path, toml_cfg: dict) -> list[dict]:
    """safe-fix 대상 파일/디렉토리 탐지. os.walk로 SKIP_DIRS 조기 가지치기."""
    items = []
    skip_dirs = _resolved_skip_dirs(toml_cfg)

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        rel_dir = os.path.relpath(dirpath, root)

        pruned = []
        for d in list(dirnames):
            if d in SAFE_DIR_NAMES:
                rel = os.path.join(rel_dir, d) if rel_dir != "." else d
                items.append({"path": rel, "type": "dir", "category": "safe"})
                pruned.append(d)
        for d in pruned:
            dirnames.remove(d)

        for f in filenames:
            if f in SAFE_FILE_NAMES or Path(f).suffix in SAFE_FILE_SUFFIXES:
                rel = os.path.join(rel_dir, f) if rel_dir != "." else f
                items.append({"path": rel, "type": "file", "category": "safe"})

    # 프로젝트별 작업용 임시 파일 패턴 (toml 옵션)
    work_temp_dir = toml_cfg.get("work_temp_dir")
    work_temp_prefixes = tuple(toml_cfg.get("work_temp_prefixes", []))
    if work_temp_dir and work_temp_prefixes:
        for entry_dir in root.glob(work_temp_dir):
            if not entry_dir.is_dir():
                continue
            for entry in entry_dir.iterdir():
                if not entry.is_file():
                    continue
                if any(entry.name.startswith(p) for p in work_temp_prefixes):
                    items.append({"path": str(entry.relative_to(root)), "type": "file", "category": "safe"})
    return items


def _scan_plans(root: Path) -> list[dict]:
    """끝난 .plans 후보 탐지.

    조건: mtime > 30일 AND (VERIFIED PASS 마커 OR DoD 체크박스 모두 완료).
    자동 삭제 X — review 항목으로 보고만.
    """
    items = []
    plans_dir = root / PLANS_DIR_NAME
    if not plans_dir.is_dir():
        return items

    age_cutoff_sec = PLANS_AGE_THRESHOLD_DAYS * 86400
    now = time.time()

    for path in plans_dir.glob("*.md"):
        if not path.is_file():
            continue
        age_sec = now - path.stat().st_mtime
        if age_sec < age_cutoff_sec:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        has_verified = bool(VERIFIED_PASS_RE.search(text))
        unchecked = len(DOD_UNCHECKED_RE.findall(text))
        checked = len(DOD_CHECKED_RE.findall(text))
        all_dod_done = checked >= 1 and unchecked == 0
        if has_verified or all_dod_done:
            reason_parts = []
            if has_verified:
                reason_parts.append("VERIFIED PASS")
            if all_dod_done:
                reason_parts.append(f"DoD {checked}/{checked} 체크")
            items.append({
                "path": str(path.relative_to(root)),
                "type": "plan_done",
                "category": "review",
                "age_days": int(age_sec / 86400),
                "reason": " + ".join(reason_parts),
            })
    return items


def _scan_handoff(root: Path) -> list[dict]:
    """stale handoff JSON 후보 탐지.

    handoff는 1회용·휘발성 — 새 세션이 부트스트랩 후 더 이상 쓸모 없음.
    조건: mtime > HANDOFF_AGE_THRESHOLD_DAYS AND kind=="handoff" 스키마.
    자동 삭제 X — review 항목으로 보고만.
    """
    items = []
    handoff_dir = root / HANDOFF_DIR
    if not handoff_dir.is_dir():
        return items

    age_cutoff_sec = HANDOFF_AGE_THRESHOLD_DAYS * 86400
    now = time.time()

    for path in handoff_dir.glob("*.json"):
        if not path.is_file():
            continue
        age_sec = now - path.stat().st_mtime
        if age_sec < age_cutoff_sec:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("kind") != "handoff":
            continue
        summary = (data.get("next_task") or {}).get("summary", "")
        items.append({
            "path": str(path.relative_to(root)),
            "type": "handoff_stale",
            "category": "review",
            "age_days": int(age_sec / 86400),
            "summary": summary[:80],
        })
    return items


def _scan_todo_ctx(root: Path) -> list[dict]:
    """stale todo-ctx 사이드카 후보 탐지 (관련 설계 결정).

    handoff와 달리 age-out 아님 — 연결 todo 종결/소멸 기준:
    - 연결 todo `#NNN` 가 `[x]` (closed, Archive 포함) → stale
    - `#NNN` 줄이 todos.md 에 아예 없음 (orphan) → stale
    - `#NNN` 가 `[ ]` (open) → 유지
    자동 삭제 X — review 항목으로 보고만 (close 전 load-bearing 결정 ADR 승격 = 졸업 게이트).
    todos.md 없으면 판정 불가 → skip (오삭제 방지).
    NNN.json 규약 아닌 파일은 건드리지 않음.
    """
    items = []
    ctx_dir = root / TODO_CTX_DIR
    todos_path = root / TODOS_PATH
    if not ctx_dir.is_dir() or not todos_path.is_file():
        return items
    try:
        todos_text = todos_path.read_text(encoding="utf-8")
    except OSError:
        return items
    open_ids = set(TODO_OPEN_RE.findall(todos_text))
    closed_ids = set(TODO_CLOSED_RE.findall(todos_text))

    for path in ctx_dir.glob("*.json"):
        if not path.is_file():
            continue
        m = TODO_CTX_FILE_RE.match(path.name)
        if not m:
            continue
        nnn = m.group(1)
        if nnn in open_ids:
            continue
        reason = f"todo #{nnn} closed" if nnn in closed_ids else f"todo #{nnn} 줄 부재 (orphan)"
        items.append({
            "path": str(path.relative_to(root)),
            "type": "todo_ctx_stale",
            "category": "review",
            "reason": reason,
        })
    return items


def _scan_review(root: Path) -> list[dict]:
    """review-fix 대상 탐지 (끝난 .plans + stale handoff + stale todo-ctx + ruff 위반).

    ruff 없는 환경에선 silent skip.
    """
    items = []
    items.extend(_scan_plans(root))
    items.extend(_scan_handoff(root))
    items.extend(_scan_todo_ctx(root))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--select", "F401,F841", "--format", "json", str(root)],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip():
            violations = json.loads(result.stdout)
            for v in violations:
                filepath = v.get("filename", "")
                try:
                    rel = str(Path(filepath).relative_to(root))
                except ValueError:
                    rel = filepath
                items.append({
                    "path": rel,
                    "type": "ruff",
                    "category": "review",
                    "code": v.get("code", ""),
                    "message": v.get("message", ""),
                    "line": v.get("location", {}).get("row", 0),
                })
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return items


def _dir_size_bytes(path: Path) -> int:
    """디렉토리 총 바이트. 권한 거부 등 에러는 무시."""
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = Path(dirpath) / f
            try:
                total += fp.stat().st_size
            except OSError:
                continue
    return total


def _detect_large_dirs(root: Path, threshold_mb: int = LARGE_DIR_THRESHOLD_MB) -> list[dict]:
    """top-level 디렉토리 중 임계 이상 크기 후보 반환.

    SKILL.md 가 첫 실행 시 호출하여 사용자에게 스캔 제외 여부 묻기 위함.
    이미 DEFAULT_SKIP_DIRS 에 든 폴더는 제외.
    """
    items = []
    threshold_bytes = threshold_mb * 1024 * 1024
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in DEFAULT_SKIP_DIRS:
            continue
        if entry.name.startswith("."):
            continue
        size = _dir_size_bytes(entry)
        if size >= threshold_bytes:
            items.append({
                "name": entry.name,
                "size_mb": round(size / (1024 * 1024), 1),
            })
    items.sort(key=lambda x: x["size_mb"], reverse=True)
    return items


def _delete_safe(items: list[dict], root: Path) -> int:
    """safe 항목 삭제. 삭제 건수 반환."""
    count = 0
    dirs = [i for i in items if i["type"] == "dir"]
    files = [i for i in items if i["type"] == "file"]

    for item in dirs:
        target = root / item["path"]
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            count += 1

    for item in files:
        target = root / item["path"]
        try:
            target.unlink()
            count += 1
        except OSError:
            pass
    return count


def main():
    parser = argparse.ArgumentParser(description="GC check — 불필요 파일 탐지/정리 (전역 스킬)")
    parser.add_argument("--safe-fix", action="store_true", help="safe 항목 자동 삭제")
    parser.add_argument("--dry-run", action="store_true", help="전체 스캔 보고 (삭제 없음)")
    parser.add_argument("--review-only", action="store_true", help="review 카테고리만 체크")
    parser.add_argument("--report-json", action="store_true", help="JSON 출력")
    parser.add_argument("--detect-large-dirs", action="store_true", help="top-level 큰 폴더 후보 보고")
    parser.add_argument("--root", type=str, default=None, help="프로젝트 루트 지정 (기본: .git 탐색)")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else _find_project_root()
    toml_cfg = _load_gc_toml(root)

    if args.detect_large_dirs:
        large = _detect_large_dirs(root)
        if args.report_json:
            print(json.dumps({"large_dirs": large, "threshold_mb": LARGE_DIR_THRESHOLD_MB}, ensure_ascii=False))
        else:
            if large:
                print(f"[gc] {LARGE_DIR_THRESHOLD_MB}MB 이상 top-level 폴더 {len(large)}개:")
                for d in large:
                    print(f"  {d['name']} ({d['size_mb']} MB)")
            else:
                print(f"[gc] {LARGE_DIR_THRESHOLD_MB}MB 이상 후보 없음")
        sys.exit(0)

    if not any([args.safe_fix, args.dry_run, args.review_only]):
        args.dry_run = True

    safe_items = []
    review_items = []

    if args.review_only:
        review_items = _scan_review(root)
    elif args.dry_run:
        safe_items = _scan_safe(root, toml_cfg)
        review_items = _scan_review(root)
    elif args.safe_fix:
        safe_items = _scan_safe(root, toml_cfg)

    if args.safe_fix and safe_items:
        deleted = _delete_safe(safe_items, root)
        if args.report_json:
            print(json.dumps({"deleted": deleted, "items": safe_items}, ensure_ascii=False))
        else:
            print(f"[gc] {deleted}건 삭제 완료")
        sys.exit(0)

    all_items = safe_items + review_items
    if args.report_json:
        print(json.dumps({"safe": safe_items, "review": review_items}, ensure_ascii=False))
    else:
        if not all_items:
            if not args.review_only:
                print("[gc] 정리 대상 없음")
        else:
            if safe_items:
                print(f"[gc] safe-fix 대상 {len(safe_items)}건:")
                for item in safe_items:
                    print(f"  {item['path']} ({item['type']})")
            if review_items:
                print(f"[gc] review 대상 {len(review_items)}건:")
                for item in review_items:
                    if item["type"] == "plan_done":
                        print(f"  {item['path']} (끝난 플랜 후보, {item['age_days']}일 경과, {item['reason']})")
                    elif item["type"] == "handoff_stale":
                        summary = item.get("summary") or "(summary 없음)"
                        print(f"  {item['path']} (stale handoff, {item['age_days']}일 경과, {summary})")
                    elif item["type"] == "todo_ctx_stale":
                        print(f"  {item['path']} (stale todo-ctx, {item['reason']})")
                    elif item["type"] == "ruff":
                        print(f"  {item['path']}:{item['line']} {item['code']} {item['message']}")
                    else:
                        print(f"  {item['path']}")

    sys.exit(0)


if __name__ == "__main__":
    main()
