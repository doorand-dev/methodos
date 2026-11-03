"""CLI regressions using synthetic input and temporary workspaces only.

Set SNAPSHOT_HELPER to exercise another installed copy with the same tests.
Run with python -B -m unittest discover -s skills/codex/snapshot/tests -v.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from datetime import datetime, timedelta, timezone


HELPER = Path(os.environ.get(
    "SNAPSHOT_HELPER",
    str(Path(__file__).resolve().parents[1] / "scripts" / "write_context_snapshot.py"),
)).resolve()

# -S excludes site packages (including installed tzdata). Block both timezone
# modules as well so the regression cannot accidentally use host IANA data.
BOOTSTRAP = """
import importlib.abc
import runpy
import sys

class NoTimezoneData(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in ('zoneinfo', 'tzdata'):
            raise ModuleNotFoundError('Timezone data deliberately unavailable')

sys.meta_path.insert(0, NoTimezoneData())
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""


class SnapshotCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.input = self.root / "input.json"
        self.payload = {
            "in_flight": {"task": "합성 작업", "next_immediate_step": "검증"},
            "active_constraints": ["synthetic data only"],
        }
        self.write_input()

    def write_input(self):
        # PowerShell-generated UTF-8 input can include a BOM.
        self.input.write_text(json.dumps(self.payload, ensure_ascii=False), encoding="utf-8-sig")

    def cli(self, *args):
        result = subprocess.run(
            [sys.executable, "-B", "-S", "-c", BOOTSTRAP, str(HELPER)] + list(args),
            cwd=str(self.root), capture_output=True, encoding="utf-8",
            env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONTZPATH=""),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def save(self, session="example-task", *extra):
        return json.loads(self.cli(
            "--input", str(self.input), "--workspace", str(self.root),
            "--session-id", session, *extra,
        ))

    def read(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_first_run_without_timezone_data(self):
        before = datetime.now(timezone.utc)
        result = self.save()
        after = datetime.now(timezone.utc)
        path = self.root / ".claude_context" / "sessions" / "example-task.json"
        self.assertEqual(Path(result["path"]), path)
        data = self.read(path)
        self.assertTrue(result["ok"])
        self.assertIsNone(result["backup"])
        self.assertEqual(data["in_flight"], self.payload["in_flight"])
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["kind"], "context_snapshot")
        self.assertEqual(data["workspace"], str(self.root))
        self.assertEqual(data["session_id"], "example-task")
        self.assertEqual(data["tool"], "Codex")
        self.assertEqual(result["tool"], "Codex")
        self.assertEqual(result["top_level_keys"], len(data))
        stamp = datetime.fromisoformat(data["created_at_local"])
        self.assertEqual(stamp.utcoffset(), timedelta(hours=9))
        self.assertLessEqual(before - timedelta(seconds=1), stamp)
        self.assertLessEqual(stamp, after)
        self.assertEqual(set(result), {
            "ok", "path", "schema_version", "kind", "tool", "backup",
            "session_id", "top_level_keys",
        })

    def test_same_id_archives_previous_json(self):
        first = self.save()
        original = Path(first["path"]).read_bytes()
        self.payload["in_flight"]["phase"] = "updated"
        self.write_input()
        second = self.save()
        backup = Path(second["backup"])
        self.assertEqual(backup.parent, self.root / ".claude_context" / "archive")
        self.assertRegex(backup.name, r"^example-task_\d{8}_\d{6}\.json$")
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(self.read(second["path"])["in_flight"]["phase"], "updated")

    def test_other_session_does_not_touch_first(self):
        first = self.save()
        original = Path(first["path"]).read_bytes()
        second = self.save("other-task")
        self.assertNotEqual(first["path"], second["path"])
        self.assertEqual(Path(first["path"]).read_bytes(), original)
        self.assertEqual(self.read(second["path"])["session_id"], "other-task")
        self.assertIsNone(second["backup"])
        self.assertFalse((self.root / ".claude_context" / "archive").exists())

    def test_explicit_fields_including_tool_are_preserved(self):
        explicit = {
            "tool": "example-client", "created_at_local": "2026-01-01T12:00:00+09:00",
            "schema_version": "custom", "kind": "custom", "workspace": "example-workspace",
            "session_id": "payload-id", "resume_instruction": "example instruction",
        }
        self.payload.update(explicit)
        self.write_input()
        result = self.save()
        data = self.read(result["path"])
        for key, value in explicit.items():
            self.assertEqual(data[key], value)
        self.assertEqual(result["tool"], explicit["tool"])

    def test_output_and_no_backup_options(self):
        first = self.save("example-task", "--output", "custom/snapshot.json")
        self.assertEqual(Path(first["path"]), self.root / "custom" / "snapshot.json")
        self.payload["in_flight"]["phase"] = "replacement"
        self.write_input()
        second = self.save("example-task", "--output", "custom/snapshot.json", "--no-backup")
        self.assertIsNone(second["backup"])
        self.assertEqual(self.read(second["path"])["in_flight"]["phase"], "replacement")
        self.assertFalse((self.root / ".claude_context" / "archive").exists())

    def test_default_workspace_and_generated_id(self):
        result = json.loads(self.cli("--input", str(self.input)))
        self.assertRegex(result["session_id"], r"^\d{8}_\d{6}$")
        self.assertEqual(Path(result["path"]), self.root / ".claude_context" / "sessions" / (result["session_id"] + ".json"))
        self.assertEqual(self.read(result["path"])["workspace"], str(self.root))

    def test_help_without_timezone_data(self):
        help_text = self.cli("--help")
        self.assertIn("Codex", help_text)
        for flag in ("--input", "--workspace", "--output", "--session-id", "--no-backup"):
            self.assertIn(flag, help_text)
        self.assertFalse((self.root / ".claude_context").exists())


if __name__ == "__main__":
    unittest.main()
