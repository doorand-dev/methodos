from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("active-models-adapter.py")
ACTIVE_SCRIPT = Path(r"C:\Users\hjcha\.codex\rules\scripts\active-models-adapter.py")
ACTIVE_CATALOG = Path(r"C:\Users\hjcha\.codex\opencodex-catalog.json")
ACTIVE_OUTPUT = Path(r"C:\Users\hjcha\.codex\active-models.json")
DEEPSEEK_FLASH = "opencode-free/deepseek-v4-flash-free"


def run_adapter(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class ActiveModelsAdapterTests(unittest.TestCase):
    def write_catalog(self, path: Path, rows: list[dict[str, object]]) -> None:
        path.write_text(json.dumps({"models": rows}), encoding="utf-8")

    def test_visible_models_are_projected_in_catalog_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "catalog.json"
            output = root / "active-models.json"
            self.write_catalog(
                source,
                [
                    {
                        "slug": "visible/one",
                        "display_name": "Visible One",
                        "visibility": "list",
                        "supported_reasoning_levels": [
                            {"effort": "low"},
                            {"effort": "high"},
                        ],
                    },
                    {
                        "slug": "hidden/two",
                        "display_name": "Hidden Two",
                        "visibility": "hide",
                        "supported_reasoning_levels": [{"effort": "medium"}],
                    },
                    {
                        "slug": "visible/three",
                        "visibility": "list",
                        "supported_reasoning_levels": [{"effort": "xhigh"}],
                    },
                ],
            )

            result = run_adapter(
                SCRIPT, "--ensure", "--source", str(source), "--output", str(output)
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            projection = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                list(projection),
                ["schemaVersion", "source", "selection", "generatedAt", "models"],
            )
            self.assertEqual(projection["schemaVersion"], 1)
            self.assertEqual(projection["source"], "catalog.json")
            self.assertEqual(projection["selection"], 'models[].visibility == "list"')
            self.assertIsInstance(projection["generatedAt"], str)
            self.assertEqual(
                projection["models"],
                [
                    {
                        "slug": "visible/one",
                        "displayName": "Visible One",
                        "reasoningEfforts": ["low", "high"],
                    },
                    {
                        "slug": "visible/three",
                        "displayName": "visible/three",
                        "reasoningEfforts": ["xhigh"],
                    },
                ],
            )

    def test_unchanged_projection_preserves_mtime_and_content(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "catalog.json"
            output = root / "active-models.json"
            self.write_catalog(
                source,
                [
                    {
                        "slug": "visible/one",
                        "display_name": "Visible One",
                        "visibility": "list",
                        "supported_reasoning_levels": [{"effort": "low"}],
                    }
                ],
            )
            first = run_adapter(SCRIPT, "--ensure", "--source", str(source), "--output", str(output))
            self.assertEqual(first.returncode, 0, first.stderr)
            before = output.read_bytes()
            before_mtime = output.stat().st_mtime_ns

            second = run_adapter(SCRIPT, "--ensure", "--source", str(source), "--output", str(output))

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(output.stat().st_mtime_ns, before_mtime)

    def test_changed_source_rewrites_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "catalog.json"
            output = root / "active-models.json"
            row = {
                "slug": "visible/one",
                "display_name": "Visible One",
                "visibility": "list",
                "supported_reasoning_levels": [{"effort": "low"}],
            }
            self.write_catalog(source, [row])
            first = run_adapter(SCRIPT, "--ensure", "--source", str(source), "--output", str(output))
            self.assertEqual(first.returncode, 0, first.stderr)
            before = output.read_bytes()
            os.utime(output, (1, 1))

            row["display_name"] = "Renamed One"
            self.write_catalog(source, [row])
            second = run_adapter(SCRIPT, "--ensure", "--source", str(source), "--output", str(output))

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertNotEqual(output.read_bytes(), before)
            self.assertNotEqual(output.stat().st_mtime_ns, 1_000_000_000)

    def test_malformed_source_preserves_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "catalog.json"
            output = root / "active-models.json"
            prior = b'{"schemaVersion":1,"models":[]}'
            output.write_bytes(prior)
            source.write_text("{ malformed", encoding="utf-8")

            result = run_adapter(SCRIPT, "--ensure", "--source", str(source), "--output", str(output))

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), prior)

    def test_live_catalog_matches_visible_slugs_and_contains_deepseek_flash(self) -> None:
        result = run_adapter(ACTIVE_SCRIPT, "--ensure")
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads(ACTIVE_CATALOG.read_text(encoding="utf-8"))
        projection = json.loads(ACTIVE_OUTPUT.read_text(encoding="utf-8"))
        expected = [
            row["slug"] for row in catalog["models"] if row["visibility"] == "list"
        ]
        actual = [model["slug"] for model in projection["models"]]
        self.assertEqual(actual, expected)
        self.assertIn(DEEPSEEK_FLASH, actual)

    def test_canonical_and_active_scripts_are_byte_identical(self) -> None:
        self.assertEqual(SCRIPT.read_bytes(), ACTIVE_SCRIPT.read_bytes())


if __name__ == "__main__":
    unittest.main()
