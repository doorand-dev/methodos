#!/usr/bin/env python3
"""Project the visible OpenCodex catalog into the small active-models file."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = Path(r"C:\Users\hjcha\.codex\opencodex-catalog.json")
DEFAULT_OUTPUT = Path(r"C:\Users\hjcha\.codex\active-models.json")
SELECTION = 'models[].visibility == "list"'


class AdapterError(ValueError):
    """Raised when the catalog cannot be projected safely."""


def _model_error(index: int, message: str) -> AdapterError:
    return AdapterError(f"invalid model row {index}: {message}")


def _load_catalog(source: Path) -> list[dict[str, Any]]:
    try:
        with source.open("r", encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"cannot read catalog {source}: {exc}") from exc

    if not isinstance(catalog, dict):
        raise AdapterError("catalog root must be an object")
    rows = catalog.get("models")
    if not isinstance(rows, list):
        raise AdapterError("catalog models must be an array")

    validated: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise _model_error(index, "row must be an object")

        slug = row.get("slug")
        if not isinstance(slug, str) or not slug:
            raise _model_error(index, "slug must be a non-empty string")

        visibility = row.get("visibility")
        if not isinstance(visibility, str):
            raise _model_error(index, "visibility must be a string")

        levels = row.get("supported_reasoning_levels")
        if not isinstance(levels, list):
            raise _model_error(index, "supported_reasoning_levels must be an array")
        for level_index, level in enumerate(levels):
            if not isinstance(level, dict):
                raise _model_error(index, f"reasoning level {level_index} must be an object")
            effort = level.get("effort")
            if not isinstance(effort, str) or not effort:
                raise _model_error(
                    index,
                    f"reasoning level {level_index} effort must be a non-empty string",
                )

        display_name = row.get("display_name", slug)
        if display_name is None or display_name == "":
            display_name = slug
        elif not isinstance(display_name, str):
            raise _model_error(index, "display_name must be a string")

        validated.append(
            {
                "slug": slug,
                "display_name": display_name,
                "visibility": visibility,
                "supported_reasoning_levels": levels,
            }
        )
    return validated


def _build_projection(source: Path) -> dict[str, Any]:
    rows = _load_catalog(source)
    models = [
        {
            "slug": row["slug"],
            "displayName": row["display_name"],
            "reasoningEfforts": [
                level["effort"] for level in row["supported_reasoning_levels"]
            ],
        }
        for row in rows
        if row["visibility"] == "list"
    ]
    return {
        "schemaVersion": 1,
        "source": source.name,
        "selection": SELECTION,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        ),
        "models": models,
    }


def _semantic_projection(document: Any) -> Any:
    if not isinstance(document, dict):
        return None
    return {key: value for key, value in document.items() if key != "generatedAt"}


def _read_existing(output: Path) -> Any:
    try:
        with output.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _write_atomically(output: Path, document: dict[str, Any]) -> None:
    temp_path: Path | None = None
    open_fd: int | None = None
    try:
        open_fd, temp_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".tmp", dir=str(output.parent)
        )
        temp_path = Path(temp_name)
        with os.fdopen(open_fd, "w", encoding="utf-8", newline="\n") as handle:
            open_fd = None
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, output)
        temp_path = None
    finally:
        if open_fd is not None:
            os.close(open_fd)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def ensure_projection(source: Path, output: Path) -> bool:
    projection = _build_projection(source)
    if _semantic_projection(_read_existing(output)) == _semantic_projection(projection):
        return False
    _write_atomically(output, projection)
    return True


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ensure", action="store_true", help="ensure the projection is current")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        ensure_projection(args.source, args.output)
    except (AdapterError, OSError, UnicodeError) as exc:
        print(f"active-models-adapter: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
