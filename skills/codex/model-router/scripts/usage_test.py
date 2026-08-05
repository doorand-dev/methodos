#!/usr/bin/env python3
"""Record task-scoped OpenCodex usage observations for model-routing tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_USAGE_LOG = Path.home() / ".opencodex" / "usage.jsonl"
DEFAULT_DATA_DIR = Path.home() / ".codex" / "usage-tests"
TASK_TYPES = (
    "exploration",
    "diagnosis",
    "implementation",
    "review",
    "data-organization",
    "image-understanding",
)
SIZES = ("small", "medium", "large")
MODALITIES = ("text", "image", "pipeline")
TASK_SHAPES = ("retrieve", "transform", "synthesize", "decide")
CONTEXT_STATES = ("packet_closed", "selected_files", "raw_corpus")
JUDGMENT_LEVELS = ("apply", "reconcile", "authority_decision")
EXECUTION_SHAPES = ("read_only", "isolated_candidate", "canonical_single_writer")
EXECUTORS = ("orchestrator", "subagent", "unknown")
DEPENDENCY_SPANS = ("single_file", "bounded_multifile", "cross_system")
COMPARISON_SCOPES = ("full-task", "bounded-slice")
OUTCOMES = (
    "ready",
    "minor-revision",
    "major-revision",
    "failed",
    "unsupported",
    "not-rated",
)
BILLING_MODES = ("subscription", "paid-api", "free", "unknown")
REVISION_BURDENS = ("none", "minor", "major", "unknown")


def emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def now_ms() -> int:
    return int(time.time() * 1000)


def data_paths(data_dir: Path) -> tuple[Path, Path]:
    runs_dir = data_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    return runs_dir, data_dir / "records.jsonl"


def file_fingerprint(raw_path: str) -> dict[str, Any]:
    path = Path(raw_path).expanduser().resolve()
    result: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists() or not path.is_file():
        return result
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    result.update({"size": path.stat().st_size, "sha256": digest.hexdigest()})
    return result


def route_parts(slug: str) -> tuple[str, str]:
    if "/" in slug:
        provider, model = slug.split("/", 1)
        return provider, model
    return "openai", slug


def start_run(args: argparse.Namespace) -> int:
    if args.route_slug:
        slug_provider, slug_model = route_parts(args.route_slug)
        if args.provider and args.provider != slug_provider:
            emit({"error": "route-slug-mismatch", "field": "provider", "slug_value": slug_provider, "supplied": args.provider})
            return 2
        if args.model and args.model != slug_model:
            emit({"error": "route-slug-mismatch", "field": "model", "slug_value": slug_model, "supplied": args.model})
            return 2
        args.provider = slug_provider
        args.model = slug_model
    if args.comparison_group and (not args.provider or not args.model):
        emit({
            "error": "route-required-at-start",
            "next": "rerun start with the candidate's exact --provider and --model; include --effort when the route has one",
        })
        return 2
    if args.comparison_group and args.executor == "unknown":
        emit({"error": "executor-required-at-start", "next": "rerun start with --executor orchestrator or --executor subagent"})
        return 2
    usage_log = Path(args.usage_log).expanduser().resolve()
    data_dir = Path(args.data_dir).expanduser().resolve()
    runs_dir, _ = data_paths(data_dir)
    run_id = uuid.uuid4().hex[:12]
    state = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "active",
        "task": args.task,
        "task_type": args.task_type,
        "task_subtype": args.task_subtype,
        "task_shape": args.task_shape,
        "context_state": args.context_state,
        "judgment_level": args.judgment_level,
        "execution_shape": args.execution_shape,
        "executor": args.executor,
        "dependency_span": args.dependency_span,
        "size": args.size,
        "modality": args.modality,
        "comparison_scope": args.comparison_scope,
        "comparison_group": args.comparison_group,
        "notes": args.notes,
        "route_lock": {"slug": args.route_slug, "provider": args.provider, "model": args.model, "effort": args.effort},
        "started_at_ms": args.baseline_start_ms if args.baseline_start_ms is not None else now_ms(),
        "usage_log": str(usage_log),
        "usage_offset": args.baseline_offset if args.baseline_offset is not None else (usage_log.stat().st_size if usage_log.exists() else 0),
        "inputs": [file_fingerprint(item) for item in args.input],
        "comparison_packet": file_fingerprint(args.packet) if args.packet else None,
    }
    state_path = runs_dir / f"{run_id}.json"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    emit(state)
    return 0


def read_appended_jsonl(path: Path, offset: int) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        size = path.stat().st_size
        handle.seek(offset if 0 <= offset <= size else 0)
        for raw_line in handle:
            try:
                row = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def filtered_rows(rows: Iterable[dict[str, Any]], args: argparse.Namespace, started_at: int) -> list[dict[str, Any]]:
    selected = []
    for row in rows:
        if int(row.get("timestamp") or 0) < started_at:
            continue
        if row.get("usageStatus") not in (None, "reported"):
            continue
        if args.conversation_id and row.get("conversationId") != args.conversation_id:
            continue
        if args.provider and row.get("provider") != args.provider:
            continue
        if args.model and row.get("model") != args.model and row.get("resolvedModel") != args.model:
            continue
        effort = row.get("effectiveEffort") or row.get("requestedEffort")
        if args.effort and effort != args.effort:
            continue
        selected.append(row)
    return sorted(selected, key=lambda row: int(row.get("timestamp") or 0))


def chain_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: int(row.get("timestamp") or 0))
    overlaps = 0
    input_decreases = 0
    max_end = -1
    previous_input: int | None = None
    efforts: Counter[str] = Counter()
    for row in ordered:
        started = int(row.get("timestamp") or 0)
        ended = started + int(row.get("durationMs") or 0)
        if max_end >= 0 and started < max_end - 300:
            overlaps += 1
        max_end = max(max_end, ended)
        input_tokens = int((row.get("usage") or {}).get("inputTokens") or 0)
        if previous_input is not None and input_tokens < previous_input - 2000:
            input_decreases += 1
        previous_input = input_tokens
        effort = row.get("effectiveEffort") or row.get("requestedEffort") or "__none__"
        efforts[str(effort)] += 1
    return {
        "serial_overlap_count": overlaps,
        "input_decrease_count": input_decreases,
        "effort_counts": dict(efforts),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    input_tokens = sum(int((row.get("usage") or {}).get("inputTokens") or 0) for row in rows)
    cached_tokens = sum(int((row.get("usage") or {}).get("cachedInputTokens") or 0) for row in rows)
    cache_read_tokens = sum(
        int(
            (row.get("usage") or {}).get("cacheReadInputTokens")
            if (row.get("usage") or {}).get("cacheReadInputTokens") is not None
            else (row.get("usage") or {}).get("cachedInputTokens") or 0
        )
        for row in rows
    )
    cache_creation_tokens = sum(int((row.get("usage") or {}).get("cacheCreationInputTokens") or 0) for row in rows)
    uncached_tokens = max(0, input_tokens - cache_read_tokens - cache_creation_tokens)
    output_tokens = sum(int((row.get("usage") or {}).get("outputTokens") or 0) for row in rows)
    reasoning_tokens = sum(int((row.get("usage") or {}).get("reasoningOutputTokens") or 0) for row in rows)
    providers = sorted({str(row.get("provider")) for row in rows if row.get("provider")})
    models = sorted({str(row.get("model") or row.get("resolvedModel")) for row in rows if row.get("model") or row.get("resolvedModel")})
    efforts = sorted({str(row.get("effectiveEffort") or row.get("requestedEffort")) for row in rows if row.get("effectiveEffort") or row.get("requestedEffort")})
    timestamps = [int(row.get("timestamp") or 0) for row in rows]
    statuses = Counter(str(row.get("status")) for row in rows)
    return {
        "requests": len(rows),
        "provider": providers[0] if len(providers) == 1 else providers,
        "model": models[0] if len(models) == 1 else models,
        "effort": efforts[0] if len(efforts) == 1 else efforts,
        "first_usage_at_ms": min(timestamps),
        "last_usage_at_ms": max(timestamps),
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "cache_read_input_tokens": cache_read_tokens,
        "cache_creation_input_tokens": cache_creation_tokens,
        "uncached_input_tokens": uncached_tokens,
        "cache_rate": round(cache_read_tokens / input_tokens, 6) if input_tokens else None,
        "output_tokens": output_tokens,
        "reasoning_output_tokens": reasoning_tokens,
        "total_tokens": input_tokens + output_tokens,
        "reported_request_duration_ms": sum(int(row.get("durationMs") or 0) for row in rows),
        "statuses": dict(statuses),
    }


def candidate_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("conversationId") or "__missing__")].append(row)
    candidates = []
    for conversation_id, grouped in groups.items():
        item = aggregate(grouped)
        item["conversation_id"] = conversation_id
        candidates.append(item)
    return sorted(candidates, key=lambda item: item["total_tokens"], reverse=True)


def route_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        provider = str(row.get("provider") or "__missing__")
        model = str(row.get("model") or row.get("resolvedModel") or "__missing__")
        groups[(provider, model)].append(row)
    routes = []
    for (provider, model), grouped in groups.items():
        item = aggregate(grouped)
        item.update({"provider": provider, "model": model, **chain_diagnostics(grouped)})
        routes.append(item)
    return sorted(routes, key=lambda item: item["total_tokens"], reverse=True)


def finish_run(args: argparse.Namespace) -> int:
    data_dir = Path(args.data_dir).expanduser().resolve()
    runs_dir, records_path = data_paths(data_dir)
    state_path = runs_dir / f"{args.run_id}.json"
    if not state_path.exists():
        emit({"error": "run-not-found", "run_id": args.run_id})
        return 2
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("status") == "finished":
        emit({"error": "run-already-finished", "run_id": args.run_id, "record_id": state.get("record_id")})
        return 2
    if args.quality_score is not None and not 0 <= args.quality_score <= 100:
        emit({"error": "quality-score-out-of-range", "run_id": args.run_id, "expected": "0..100"})
        return 2
    if args.rank is not None and args.rank < 1:
        emit({"error": "rank-out-of-range", "run_id": args.run_id, "expected": ">=1"})
        return 2
    if args.tool_rounds is not None and args.tool_rounds < 0:
        emit({"error": "tool-rounds-out-of-range", "run_id": args.run_id, "expected": ">=0"})
        return 2
    route_lock = state.get("route_lock") or {}
    for field in ("provider", "model", "effort"):
        locked = route_lock.get(field)
        supplied = getattr(args, field)
        if locked and supplied and locked != supplied:
            emit({"error": "route-lock-mismatch", "run_id": args.run_id, "field": field, "locked": locked, "supplied": supplied})
            return 2
        if locked and not supplied:
            setattr(args, field, locked)
    usage_log = Path(state["usage_log"])
    appended = read_appended_jsonl(usage_log, int(state["usage_offset"]))
    if not args.provider or not args.model:
        candidates = candidate_summaries(filtered_rows(appended, args, int(state["started_at_ms"])))
        emit({
            "error": "route-unverified",
            "run_id": args.run_id,
            "candidates": candidates,
            "next": "rerun finish with the exact --provider, --model, and --effort; candidate ordering is not session identity",
        })
        return 2
    rows = filtered_rows(appended, args, int(state["started_at_ms"]))
    candidates = candidate_summaries(rows)
    if not rows:
        emit({"error": "no-matching-usage", "run_id": args.run_id})
        return 2
    if not args.conversation_id and len(candidates) > 1:
        emit({"error": "ambiguous-conversation", "run_id": args.run_id, "candidates": candidates})
        return 2
    selected_conversation = args.conversation_id or candidates[0]["conversation_id"]
    selected = [row for row in rows if str(row.get("conversationId") or "__missing__") == selected_conversation]
    routes = route_summaries(selected)
    if len(routes) > 1:
        emit({
            "error": "mixed-route",
            "run_id": args.run_id,
            "conversation_id": selected_conversation,
            "routes": routes,
            "next": "rerun finish with --conversation-id, --provider, --model, and --effort for exactly one route",
        })
        return 2
    diagnostics = chain_diagnostics(selected)
    if diagnostics["serial_overlap_count"] or diagnostics["input_decrease_count"]:
        emit({
            "error": "concurrent-sessions-detected",
            "run_id": args.run_id,
            "conversation_id": selected_conversation,
            **diagnostics,
            "next": "narrow the measurement window or isolate the candidate; do not record this mixed chain",
        })
        return 2
    finished_at = now_ms()
    record_id = uuid.uuid4().hex[:12]
    record = {
        "schema_version": 1,
        "record_id": record_id,
        "run_id": args.run_id,
        "measurement_scope": "through_finish",
        "task": state["task"],
        "task_type": state["task_type"],
        "task_subtype": state.get("task_subtype"),
        "task_shape": state.get("task_shape"),
        "context_state": state.get("context_state"),
        "judgment_level": state.get("judgment_level"),
        "execution_shape": state.get("execution_shape"),
        "executor": state.get("executor", "unknown"),
        "dependency_span": state.get("dependency_span"),
        "size": state["size"],
        "modality": state["modality"],
        "comparison_scope": state.get("comparison_scope", "full-task"),
        "comparison_group": state.get("comparison_group"),
        "notes": state.get("notes"),
        "finish_notes": args.finish_notes,
        "inputs": state.get("inputs", []),
        "comparison_packet": state.get("comparison_packet"),
        "conversation_id": selected_conversation,
        "route_slug": route_lock.get("slug"),
        "attribution_status": "route-locked-chain-clean" if route_lock.get("provider") and route_lock.get("model") else "finish-route-only-chain-clean",
        **diagnostics,
        "started_at_ms": state["started_at_ms"],
        "finished_at_ms": finished_at,
        "wall_duration_seconds": round((finished_at - int(state["started_at_ms"])) / 1000, 3),
        **aggregate(selected),
        "billing_mode": args.billing_mode,
        "credits_used": args.credits_used,
        "usd_cost": args.usd_cost,
        "api_equivalent_usd": args.api_equivalent_usd,
        "estimated_standard_credits": args.estimated_standard_credits,
        "credit_promotion_factor": args.credit_promotion_factor,
        "estimated_credits": args.estimated_credits,
        "estimated_subscription_usd": args.estimated_subscription_usd,
        "estimate_basis": args.estimate_basis,
        "promotion_basis": args.promotion_basis,
        "pricing_basis": args.pricing_basis,
        "pricing_as_of": args.pricing_as_of,
        "charge_source": args.charge_source,
        "outcome": args.outcome,
        "quality_score": args.quality_score,
        "rank": args.rank,
        "revision_burden": args.revision_burden,
        "evidence": args.evidence,
        "tool_rounds": args.tool_rounds,
        "retries": args.retries,
        "artifacts": [str(Path(item).expanduser().resolve()) for item in args.artifact],
        "supersedes": args.supersedes,
    }
    records_path.parent.mkdir(parents=True, exist_ok=True)
    with records_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    state.update({"status": "finished", "finished_at_ms": finished_at, "record_id": record_id})
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    emit(record)
    return 0


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                records.append(item)
    return records


def canonical_records(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    superseded = {
        str(record_id)
        for row in rows
        for record_id in (row.get("supersedes") or [])
        if record_id
    }
    latest_by_run: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("run_id") or row.get("record_id") or id(row))
        latest_by_run[key] = row
    latest = [row for row in latest_by_run.values() if str(row.get("record_id")) not in superseded]
    valid = []
    invalid_scope = 0
    for row in latest:
        if row.get("measurement_scope") == "through_finish" and int(row.get("last_usage_at_ms") or 0) > int(row.get("finished_at_ms") or 0):
            invalid_scope += 1
            continue
        valid.append(row)
    return valid, {
        "raw_records": len(rows),
        "superseded_records": len(rows) - len(latest),
        "invalid_scope_records": invalid_scope,
    }


def summary(args: argparse.Namespace) -> int:
    _, records_path = data_paths(Path(args.data_dir).expanduser().resolve())
    rows, record_health = canonical_records(load_records(records_path))
    if args.task_type:
        rows = [row for row in rows if row.get("task_type") == args.task_type]
    if args.comparison_group:
        rows = [row for row in rows if row.get("comparison_group") == args.comparison_group]
    for field in ("task_shape", "context_state", "judgment_level", "execution_shape", "executor", "dependency_span", "size", "modality"):
        value = getattr(args, field)
        if value:
            rows = [row for row in rows if (row.get(field) or "unknown") == value]
    packet_hashes: dict[str, set[str]] = defaultdict(set)
    packet_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    control_signatures: dict[str, set[tuple[str, ...]]] = defaultdict(set)
    group_executors: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        group = row.get("comparison_group")
        packet_hash = (row.get("comparison_packet") or {}).get("sha256")
        if group:
            group_counts[str(group)] += 1
            group_executors[str(group)].add(str(row.get("executor") or "unknown"))
            control_signatures[str(group)].add(tuple(str(row.get(field) or "unknown") for field in (
                "task_type", "task_shape", "context_state", "judgment_level", "execution_shape",
                "dependency_span", "size", "modality", "comparison_scope",
            )))
            if packet_hash:
                packet_counts[str(group)] += 1
                packet_hashes[str(group)].add(str(packet_hash))
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        provider = row.get("provider") if isinstance(row.get("provider"), str) else "mixed"
        model = row.get("model") if isinstance(row.get("model"), str) else "mixed"
        effort = row.get("effort") if isinstance(row.get("effort"), str) else "mixed"
        group = row.get("comparison_group")
        packet_hash = (row.get("comparison_packet") or {}).get("sha256")
        comparison_validity = "controlled" if group and group_counts[str(group)] >= 2 and packet_counts[str(group)] == group_counts[str(group)] and len(packet_hashes[str(group)]) == 1 and group_executors[str(group)] == {"subagent"} and len(control_signatures[str(group)]) == 1 else "operational"
        grouped[(
            str(row.get("task_type") or "unknown"),
            str(row.get("task_shape") or "unknown"),
            str(row.get("context_state") or "unknown"),
            str(row.get("judgment_level") or "unknown"),
            str(row.get("execution_shape") or "unknown"),
            str(row.get("executor") or "unknown"),
            comparison_validity,
            provider,
            model,
            effort,
        )].append(row)
    result = []
    for key, items in grouped.items():
        rated = [item for item in items if item.get("outcome") != "not-rated"]
        usable = [item for item in rated if item.get("outcome") in ("ready", "minor-revision")]
        known_credits = [float(item["credits_used"]) for item in items if item.get("credits_used") is not None]
        known_api_equivalent = [float(item["api_equivalent_usd"]) for item in items if item.get("api_equivalent_usd") is not None]
        known_estimated_standard_credits = [float(item["estimated_standard_credits"]) for item in items if item.get("estimated_standard_credits") is not None]
        known_estimated_credits = [float(item["estimated_credits"]) for item in items if item.get("estimated_credits") is not None]
        known_estimated_subscription = [float(item["estimated_subscription_usd"]) for item in items if item.get("estimated_subscription_usd") is not None]
        known_quality = [float(item["quality_score"]) for item in items if item.get("quality_score") is not None]
        known_tool_rounds = [int(item["tool_rounds"]) for item in items if item.get("tool_rounds") is not None]
        revision_burdens = Counter(str(item.get("revision_burden") or "unknown") for item in items)
        result.append({
            "task_type": key[0],
            "task_shape": key[1],
            "context_state": key[2],
            "judgment_level": key[3],
            "execution_shape": key[4],
            "executor": key[5],
            "comparison_validity": key[6],
            "provider": key[7],
            "model": key[8],
            "effort": key[9],
            "tasks": len(items),
            "rated_tasks": len(rated),
            "usable_rate": round(len(usable) / len(rated), 4) if rated else None,
            "total_tokens": sum(int(item.get("total_tokens") or 0) for item in items),
            "total_credits_known": round(sum(known_credits), 9) if known_credits else None,
            "total_api_equivalent_usd_known": round(sum(known_api_equivalent), 9) if known_api_equivalent else None,
            "api_equivalent_unknown_tasks": len(items) - len(known_api_equivalent),
            "total_estimated_standard_credits_known": round(sum(known_estimated_standard_credits), 9) if known_estimated_standard_credits else None,
            "total_estimated_credits_known": round(sum(known_estimated_credits), 9) if known_estimated_credits else None,
            "total_estimated_subscription_usd_known": round(sum(known_estimated_subscription), 9) if known_estimated_subscription else None,
            "mean_quality_score": round(sum(known_quality) / len(known_quality), 3) if known_quality else None,
            "revision_burdens": dict(revision_burdens),
            "median_tool_rounds": sorted(known_tool_rounds)[len(known_tool_rounds) // 2] if known_tool_rounds else None,
            "median_wall_seconds": sorted(float(item.get("wall_duration_seconds") or 0) for item in items)[len(items) // 2],
        })
    emit({"records": len(rows), **record_health, "routes": sorted(result, key=lambda item: (-item["tasks"], item["provider"], item["model"]))})
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--data-dir", default=os.fspath(DEFAULT_DATA_DIR))
    sub = root.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start")
    start.add_argument("--task", required=True)
    start.add_argument("--task-type", required=True, choices=TASK_TYPES)
    start.add_argument("--task-subtype")
    start.add_argument("--task-shape", required=True, choices=TASK_SHAPES)
    start.add_argument("--context-state", required=True, choices=CONTEXT_STATES)
    start.add_argument("--judgment-level", required=True, choices=JUDGMENT_LEVELS)
    start.add_argument("--execution-shape", required=True, choices=EXECUTION_SHAPES)
    start.add_argument("--executor", default="unknown", choices=EXECUTORS)
    start.add_argument("--dependency-span", required=True, choices=DEPENDENCY_SPANS)
    start.add_argument("--size", required=True, choices=SIZES)
    start.add_argument("--modality", default="text", choices=MODALITIES)
    start.add_argument("--comparison-scope", default="full-task", choices=COMPARISON_SCOPES)
    start.add_argument("--comparison-group")
    start.add_argument("--route-slug")
    start.add_argument("--provider")
    start.add_argument("--model")
    start.add_argument("--effort")
    start.add_argument("--notes")
    start.add_argument("--packet")
    start.add_argument("--input", action="append", default=[])
    start.add_argument("--usage-log", default=os.fspath(DEFAULT_USAGE_LOG))
    start.add_argument("--baseline-start-ms", type=int, help="Recovery only: override the captured start time")
    start.add_argument("--baseline-offset", type=int, help="Recovery only: override the usage-log byte offset")
    start.set_defaults(func=start_run)

    finish = sub.add_parser("finish")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--conversation-id")
    finish.add_argument("--provider")
    finish.add_argument("--model")
    finish.add_argument("--effort")
    finish.add_argument("--outcome", required=True, choices=OUTCOMES)
    finish.add_argument("--billing-mode", default="unknown", choices=BILLING_MODES)
    finish.add_argument("--credits-used", type=float)
    finish.add_argument("--usd-cost", type=float)
    finish.add_argument("--api-equivalent-usd", type=float)
    finish.add_argument("--estimated-standard-credits", type=float)
    finish.add_argument("--credit-promotion-factor", type=float)
    finish.add_argument("--estimated-credits", type=float)
    finish.add_argument("--estimated-subscription-usd", type=float)
    finish.add_argument("--estimate-basis")
    finish.add_argument("--promotion-basis")
    finish.add_argument("--pricing-basis")
    finish.add_argument("--pricing-as-of")
    finish.add_argument("--charge-source", choices=("dashboard", "api", "cli", "estimated", "unknown"), default="unknown")
    finish.add_argument("--quality-score", type=float)
    finish.add_argument("--rank", type=int)
    finish.add_argument("--revision-burden", choices=REVISION_BURDENS, default="unknown")
    finish.add_argument("--evidence", action="append", default=[])
    finish.add_argument("--finish-notes")
    finish.add_argument("--tool-rounds", type=int)
    finish.add_argument("--retries", type=int, default=0)
    finish.add_argument("--artifact", action="append", default=[])
    finish.add_argument("--supersedes", action="append", default=[])
    finish.set_defaults(func=finish_run)

    report = sub.add_parser("summary")
    report.add_argument("--task-type", choices=TASK_TYPES)
    report.add_argument("--task-shape", choices=TASK_SHAPES)
    report.add_argument("--context-state", choices=CONTEXT_STATES)
    report.add_argument("--judgment-level", choices=JUDGMENT_LEVELS)
    report.add_argument("--execution-shape", choices=EXECUTION_SHAPES)
    report.add_argument("--executor", choices=EXECUTORS)
    report.add_argument("--dependency-span", choices=DEPENDENCY_SPANS)
    report.add_argument("--size", choices=SIZES)
    report.add_argument("--modality", choices=MODALITIES)
    report.add_argument("--comparison-group")
    report.set_defaults(func=summary)
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
