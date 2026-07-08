"""GC 감사 — ast 기반 죽은 코드·중복 함수 탐지 (전역 스킬).

본 레포 의존 0 — 어느 워크스페이스에서든 동작.

/gc 스킬에서 호출. 프로젝트 전체 .py 파일을 AST 파싱하여:
1. 정의되었지만 어디서도 참조되지 않는 함수/클래스 (죽은 코드)
2. 함수 body가 동일한 cross-file 중복

결과를 <root>/.claude/gc_report.md 에 기록. <root>/.claude/gc.toml 의
skip_dirs 가 있으면 추가 SKIP.
"""
import ast
import hashlib
import os
import re
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    tomllib = None

DEFAULT_SKIP_DIRS = {".git", ".claude", "node_modules", ".venv", "venv", "__pycache__"}

DEFAULT_THRESHOLDS = {
    "file_lines": 400,
    "function_lines": 80,
}


def _find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".git").exists():
            return p
        p = p.parent
    return Path.cwd()


def _load_skip_dirs(root: Path) -> set[str]:
    skip = set(DEFAULT_SKIP_DIRS)
    toml_path = root / ".claude" / "gc.toml"
    if not toml_path.is_file() or tomllib is None:
        return skip
    try:
        with toml_path.open("rb") as f:
            cfg = tomllib.load(f)
        skip |= set(cfg.get("skip_dirs", []))
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return skip


def _load_thresholds(root: Path) -> dict[str, int]:
    thresholds = dict(DEFAULT_THRESHOLDS)
    toml_path = root / ".claude" / "gc.toml"
    if not toml_path.is_file() or tomllib is None:
        return thresholds
    try:
        with toml_path.open("rb") as f:
            cfg = tomllib.load(f)
        user = cfg.get("thresholds", {})
        for k, v in user.items():
            if k in thresholds and isinstance(v, int) and v > 0:
                thresholds[k] = v
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return thresholds


def _find_oversized(
    sources: dict[Path, str],
    root: Path,
    thresholds: dict[str, int],
) -> tuple[list[dict], list[dict]]:
    """누더기 방지 4단계 ③ 임계치 트리거 — 파일·함수 줄 수 초과 보고."""
    big_files: list[dict] = []
    big_funcs: list[dict] = []
    for fpath, source in sources.items():
        rel = str(fpath.relative_to(root)).replace("\\", "/")
        line_count = source.count("\n") + 1
        if line_count > thresholds["file_lines"]:
            big_files.append({"file": rel, "lines": line_count})
        try:
            tree = ast.parse(source, filename=str(fpath))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", None)
                if end is None:
                    continue
                func_lines = end - node.lineno + 1
                if func_lines > thresholds["function_lines"]:
                    big_funcs.append({
                        "name": node.name,
                        "file": rel,
                        "line": node.lineno,
                        "lines": func_lines,
                    })
    return big_files, big_funcs


def _collect_py_files(root: Path, skip_dirs: set[str]) -> list[Path]:
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(Path(dirpath) / f)
    return py_files


def _parse_definitions(py_files: list[Path], root: Path) -> tuple[dict[str, list[dict]], dict[Path, str]]:
    defs: dict[str, list[dict]] = {}
    sources: dict[Path, str] = {}
    for fpath in py_files:
        try:
            source = fpath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(fpath))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        sources[fpath] = source
        rel = str(fpath.relative_to(root)).replace("\\", "/")
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if name.startswith("_") and name != "__init__":
                    continue
                body_src = ast.get_source_segment(source, node)
                body_hash = hashlib.md5((body_src or "").encode()).hexdigest()[:12] if body_src else ""
                entry = {"file": rel, "line": node.lineno, "type": "func", "body_hash": body_hash}
                defs.setdefault(name, []).append(entry)
            elif isinstance(node, ast.ClassDef):
                name = node.name
                if name.startswith("_"):
                    continue
                entry = {"file": rel, "line": node.lineno, "type": "class", "body_hash": ""}
                defs.setdefault(name, []).append(entry)
    return defs, sources


def _build_file_tokens(sources: dict[Path, str], root: Path) -> dict[str, set[str]]:
    file_tokens: dict[str, set[str]] = {}
    for fpath, source in sources.items():
        rel = str(fpath.relative_to(root)).replace("\\", "/")
        file_tokens[rel] = set(re.findall(r'\b\w+\b', source))
    return file_tokens


def _find_dead_code(defs: dict[str, list[dict]], file_tokens: dict[str, set[str]]) -> list[dict]:
    dead = []
    for name, entries in defs.items():
        if name in ("main", "setup", "teardown", "conftest"):
            continue
        def_files = {e["file"] for e in entries}
        referenced_externally = any(
            name in tokens
            for rel, tokens in file_tokens.items()
            if rel not in def_files
        )
        if not referenced_externally:
            for entry in entries:
                dead.append({"name": name, **entry})
    return dead


def _find_duplicates(defs: dict[str, list[dict]]) -> list[dict]:
    hash_groups: dict[str, list[dict]] = {}
    for name, entries in defs.items():
        for entry in entries:
            if entry["body_hash"] and entry["type"] == "func":
                h = entry["body_hash"]
                hash_groups.setdefault(h, []).append({"name": name, **entry})

    duplicates = []
    for h, group in hash_groups.items():
        if len(group) < 2:
            continue
        files = {e["file"] for e in group}
        if len(files) < 2:
            continue
        duplicates.append({"hash": h, "entries": group})
    return duplicates


def main():
    root = _find_project_root()
    skip_dirs = _load_skip_dirs(root)
    thresholds = _load_thresholds(root)
    report_path = root / ".claude" / "gc_report.md"

    py_files = _collect_py_files(root, skip_dirs)
    defs, sources = _parse_definitions(py_files, root)
    file_tokens = _build_file_tokens(sources, root)
    dead = _find_dead_code(defs, file_tokens)
    dupes = _find_duplicates(defs)
    big_files, big_funcs = _find_oversized(sources, root, thresholds)

    lines = ["# GC Audit Report\n"]

    if dead:
        lines.append(f"## 죽은 코드 후보 ({len(dead)}건)\n")
        lines.append("| 이름 | 파일 | 줄 | 유형 |")
        lines.append("|------|------|-----|------|")
        for item in sorted(dead, key=lambda x: (x["file"], x["line"])):
            lines.append(f"| `{item['name']}` | `{item['file']}` | {item['line']} | {item['type']} |")
        lines.append("")
    else:
        lines.append("## 죽은 코드 후보: 없음\n")

    if dupes:
        lines.append(f"## Cross-file 중복 함수 ({len(dupes)}건)\n")
        for dupe in dupes:
            names = ", ".join(f"`{e['name']}`" for e in dupe["entries"])
            locs = " / ".join(f"`{e['file']}:{e['line']}`" for e in dupe["entries"])
            lines.append(f"- {names} @ {locs}")
        lines.append("")
    else:
        lines.append("## Cross-file 중복: 없음\n")

    # 누더기 방지 4단계 ③ — 임계치 초과 보고
    if big_files or big_funcs:
        lines.append(
            f"## 임계치 초과 (파일 > {thresholds['file_lines']}줄 / 함수 > {thresholds['function_lines']}줄)\n"
        )
        if big_files:
            lines.append(f"### 큰 파일 ({len(big_files)}건)\n")
            lines.append("| 파일 | 줄 수 |")
            lines.append("|------|-------|")
            for item in sorted(big_files, key=lambda x: -x["lines"]):
                lines.append(f"| `{item['file']}` | {item['lines']} |")
            lines.append("")
        if big_funcs:
            lines.append(f"### 큰 함수 ({len(big_funcs)}건)\n")
            lines.append("| 이름 | 파일 | 줄 | 길이 |")
            lines.append("|------|------|-----|------|")
            for item in sorted(big_funcs, key=lambda x: -x["lines"]):
                lines.append(
                    f"| `{item['name']}` | `{item['file']}` | {item['line']} | {item['lines']} |"
                )
            lines.append("")
        lines.append(
            "> 임계치 초과는 *리팩토링 후보 신호*. 매 단위마다 심의 X — *커진 것*만.\n"
            "> 임계치 조정: `.claude/gc.toml`의 `[thresholds]` 섹션.\n"
        )
    else:
        lines.append(
            f"## 임계치 초과: 없음 (파일 ≤ {thresholds['file_lines']}줄 / 함수 ≤ {thresholds['function_lines']}줄)\n"
        )

    report = "\n".join(lines)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(
        f"[gc-audit] 죽은 코드 {len(dead)}건, 중복 {len(dupes)}건, "
        f"큰 파일 {len(big_files)}건, 큰 함수 {len(big_funcs)}건"
    )
    if dead or dupes or big_files or big_funcs:
        try:
            rel = report_path.relative_to(root)
        except ValueError:
            rel = report_path
        print(f"  상세: {rel}")


if __name__ == "__main__":
    main()
