"""Offline regressions; all filesystem writes stay in TemporaryDirectory fixtures."""
import contextlib
import importlib.util
import io
import itertools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


GC = Path(__file__).resolve().parents[1]
REPO = GC.parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, GC / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load("gc_check")
audit = load("gc_audit")


class GcSafetyTests(unittest.TestCase):
    def test_new_and_legacy_handoff_are_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expected = set()
            for folder in (".codex_context", ".claude_context"):
                path = root / folder / "handoff" / "old.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"kind": "handoff", "next_task": {"summary": "keep evidence"}}), encoding="utf-8")
                os.utime(path, (1, 1))
                expected.add(str(path.relative_to(root)))
                fresh = path.with_name("fresh.json")
                fresh.write_text('{"kind": "handoff"}', encoding="utf-8")
            result = check._scan_handoff(root)
            self.assertEqual({item["path"] for item in result}, expected)
            self.assertTrue(all(item["category"] == "review" for item in result))
            self.assertTrue(all((root / path).is_file() for path in expected))

    def test_modes_rejected_before_any_scan_or_delete(self):
        modes = ["--dry-run", "--safe-fix", "--review-only",
                 "--detect-large-dirs", "--state-files"]
        for pair in itertools.combinations(modes, 2):
            with self.subTest(pair=pair), patch.object(sys, "argv", ["gc", *pair]), \
                    patch.object(check, "_find_project_root") as root, \
                    patch.object(check, "_scan_safe") as scan, \
                    patch.object(check, "_scan_review") as review, \
                    patch.object(check, "_delete_safe") as delete, \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exc:
                    check.main()
                self.assertEqual(exc.exception.code, 2)
                root.assert_not_called()
                scan.assert_not_called()
                review.assert_not_called()
                delete.assert_not_called()

    def test_explicit_and_default_dry_run_never_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "preserve.tmp"
            candidate.write_text("preserve", encoding="utf-8")
            for flags in ([], ["--dry-run"]):
                output = io.StringIO()
                with self.subTest(flags=flags), \
                        patch.object(sys, "argv", ["gc", "--root", tmp, "--report-json", *flags]), \
                        patch.object(check, "_scan_review", return_value=[]), \
                        patch.object(check, "_delete_safe") as delete, \
                        contextlib.redirect_stdout(output):
                    with self.assertRaises(SystemExit) as exc:
                        check.main()
                    self.assertEqual(exc.exception.code, 0)
                    delete.assert_not_called()
                    self.assertEqual(candidate.read_text(), "preserve")
                    self.assertEqual(json.loads(output.getvalue())["safe"][0]["path"], "preserve.tmp")

    def test_safe_fix_retains_explicit_delete_call(self):
        item = {"path": "only-mocked.tmp", "type": "file", "category": "safe"}
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(sys, "argv", ["gc", "--root", tmp, "--safe-fix", "--report-json"]), \
                patch.object(check, "_scan_safe", return_value=[item]), \
                patch.object(check, "_scan_review") as review, \
                patch.object(check, "_delete_safe", return_value=1) as delete, \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                check.main()
            delete.assert_called_once_with([item], Path(tmp).resolve())
            review.assert_not_called()

    def scan_ruff(self, result=None, error=None):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(check.subprocess, "run", return_value=result, side_effect=error) as run:
            items = check._scan_review(Path(tmp))
            self.assertIn("--output-format", run.call_args.args[0])
            self.assertNotIn("--format", run.call_args.args[0])
            return items

    def test_ruff_clean_output_unchanged(self):
        self.assertEqual(self.scan_ruff(subprocess.CompletedProcess([], 0, "[]", "")), [])

    def test_ruff_findings_output_unchanged(self):
        diagnostic = {"filename": "example.py", "code": "F401", "message": "unused",
                      "location": {"row": 3}}
        self.assertEqual(self.scan_ruff(subprocess.CompletedProcess([], 1, json.dumps([diagnostic]), "")),
                         [{"path": "example.py", "type": "ruff", "category": "review",
                           "code": "F401", "message": "unused", "line": 3}])

    @unittest.skipUnless(importlib.util.find_spec("ruff"), "Ruff not installed")
    def test_installed_ruff_clean_and_findings_on_temporary_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "example.py"
            source.write_text("value = 1\n", encoding="utf-8")
            self.assertEqual(check._scan_review(root), [])
            source.write_text("import os\n", encoding="utf-8")
            items = check._scan_review(root)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["code"], "F401")
            self.assertEqual(items[0]["type"], "ruff")
            self.assertEqual(source.read_text(), "import os\n")

    def test_ruff_failure_and_invalid_output_report_incomplete(self):
        for result in [subprocess.CompletedProcess([], 2, "[]", "bad arguments"),
                       subprocess.CompletedProcess([], 1, "", "No module named ruff"),
                       subprocess.CompletedProcess([], 0, "not-json", ""),
                       subprocess.CompletedProcess([], 0, "{}", ""),
                       subprocess.CompletedProcess([], 1, '[{"filename": "a", "location": null}]', "")]:
            with self.subTest(result=result):
                items = self.scan_ruff(result)
                self.assertEqual(items[0]["type"], "check_incomplete")
                self.assertIn("검사 누락", items[0]["message"])

    def test_ruff_unavailable_and_timeout_report_incomplete(self):
        for error in [FileNotFoundError("missing"), PermissionError("denied"),
                      subprocess.TimeoutExpired("ruff", 30)]:
            with self.subTest(error=error):
                self.assertEqual(self.scan_ruff(error=error)[0]["type"], "check_incomplete")

    def test_incomplete_is_visible_in_text_and_json(self):
        item = {"path": ".", "type": "check_incomplete", "category": "review",
                "check": "ruff", "message": "Ruff 검사 누락: failure"}
        for flags in ([], ["--report-json"]):
            output = io.StringIO()
            with tempfile.TemporaryDirectory() as tmp, \
                    patch.object(sys, "argv", ["gc", "--root", tmp, "--review-only", *flags]), \
                    patch.object(check, "_scan_review", return_value=[item]), \
                    contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    check.main()
            if flags:
                self.assertEqual(json.loads(output.getvalue())["review"], [item])
            else:
                self.assertIn(item["message"], output.getvalue())

    def test_audit_same_file_helper_is_never_claimed_dead(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "used.py").write_text("def helper():\n    return 1\n\ndef main():\n    return helper()\n")
            output = io.StringIO()
            with patch.object(audit, "_find_project_root", return_value=root), \
                    contextlib.redirect_stdout(output):
                audit.main()
            report = (root / ".claude/gc_report.md").read_text(encoding="utf-8")
            self.assertIn("helper", report)
            self.assertIn("외부 파일 참조 미발견", report)
            self.assertIn("정의 파일 내부 사용·동적 호출", report)
            self.assertNotIn("죽은 코드", report + output.getvalue())

    def test_audit_external_reference_excludes_candidate(self):
        defs = {"helper": [{"file": "a.py", "line": 1}]}
        self.assertEqual(audit._find_dead_code(defs, {"a.py": {"helper"}, "b.py": {"helper"}}), [])


@unittest.skipUnless(os.name == "nt" and shutil.which("powershell"), "Windows PowerShell required")
class RruleSafetyTests(unittest.TestCase):
    helpers = [REPO / "contract/codex/rules/scripts/codex-heartbeat-rrule.ps1",
               REPO / "skills/codex/ask-chatgpt-pro/scripts/codex-heartbeat-rrule.ps1"]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.profile = Path(self.temp.name)
        self.env = {**os.environ, "USERPROFILE": str(self.profile)}
        # The wrapper delegates only to this isolated copy, never the installed helper.
        global_helper = self.profile / ".codex/rules/scripts/codex-heartbeat-rrule.ps1"
        global_helper.parent.mkdir(parents=True)
        shutil.copyfile(self.helpers[0], global_helper)
        self.root = self.profile / ".codex/automations"
        self.target = self.root / "audit-job_1.2/automation.toml"
        self.target.parent.mkdir(parents=True)
        self.original = b'name = "fixture"\nrrule = "old"\nstatus = "PAUSED"\nupdated_at = 1\n'
        self.target.write_bytes(self.original)

    def invoke(self, helper, *args):
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                               str(helper), *args], env=self.env, capture_output=True, timeout=20)

    def test_generation_preserves_json_and_does_not_write(self):
        for helper in self.helpers:
            for args, seconds in [(["-DelaySeconds", "20"], 20), (["-DelayMinutes", "90"], 5400)]:
                with self.subTest(helper=helper, args=args):
                    result = self.invoke(helper, *args)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    data = json.loads(result.stdout)
                    self.assertEqual(data["delaySeconds"], seconds)
                    self.assertFalse(data["applied"])
                    self.assertIsNone(data["toml"])
                    self.assertIn("COUNT=1", data["rrule"])
                    self.assertEqual(self.target.read_bytes(), self.original)

    def test_apply_updates_only_isolated_fixture(self):
        for helper in self.helpers:
            with self.subTest(helper=helper):
                self.target.write_bytes(self.original)
                result = self.invoke(helper, "-DelayMinutes", "2", "-AutomationId", "audit-job_1.2", "-Apply")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(result.stdout)
                self.assertTrue(data["applied"])
                self.assertEqual(Path(data["toml"]), self.target)
                content = self.target.read_text()
                self.assertIn('status = "ACTIVE"', content)
                self.assertIn('rrule = "' + data["rrule"] + '"', content)
                self.assertIn('name = "fixture"', content)

    def test_unsafe_components_rejected_without_write(self):
        escape = self.profile / ".codex/automations-escape/audit/automation.toml"
        escape.parent.mkdir(parents=True)
        escape.write_bytes(self.original)
        ids = ["../automations-escape/audit", "..\\automations-escape\\audit", "a/b", "a\\b",
               ".", "..", "C:\\escape", "C:escape", "\\\\host\\share", "job:stream", "job.",
               "job ", " job", "CON", "NUL.txt", "COM1", "a*", "a?", "a[1]/b"]
        for helper in self.helpers:
            for automation_id in ids:
                with self.subTest(helper=helper, automation_id=automation_id):
                    result = self.invoke(helper, "-DelaySeconds", "10", "-AutomationId", automation_id, "-Apply")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.target.read_bytes(), self.original)
                    self.assertEqual(escape.read_bytes(), self.original)

    def test_missing_id_and_missing_target_rejected(self):
        for helper in self.helpers:
            for extra in [[], ["-AutomationId", "nonexistent"]]:
                with self.subTest(helper=helper, extra=extra):
                    result = self.invoke(helper, "-DelaySeconds", "10", "-Apply", *extra)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.target.read_bytes(), self.original)

    def test_powershell_parser_accepts_both_helpers(self):
        for helper in self.helpers:
            with self.subTest(helper=helper):
                result = subprocess.run(["powershell", "-NoProfile", "-Command",
                                         "$tokens = $null; $errors = $null; "
                                         "[System.Management.Automation.Language.Parser]::ParseFile("
                                         "$env:RRULE_SCRIPT, [ref]$tokens, [ref]$errors) | Out-Null; "
                                         "if ($errors.Count) { $errors | Out-String | Write-Error; exit 1 }"],
                                        env={**self.env, "RRULE_SCRIPT": str(helper)}, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_directory_junction_rejected_at_each_boundary(self):
        for boundary in ("job", "root", "codex"):
            with self.subTest(boundary=boundary), tempfile.TemporaryDirectory() as fixture:
                profile = Path(fixture)
                outside = profile / "outside"
                outside.mkdir()
                if boundary == "job":
                    link = profile / ".codex/automations/audit"
                    target = outside / "automation.toml"
                elif boundary == "root":
                    link = profile / ".codex/automations"
                    target = outside / "audit/automation.toml"
                else:
                    link = profile / ".codex"
                    target = outside / "automations/audit/automation.toml"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.original)
                link.parent.mkdir(parents=True, exist_ok=True)
                create = subprocess.run(["powershell", "-NoProfile", "-Command",
                                         "New-Item -ItemType Junction -Path $env:RRULE_LINK -Target $env:RRULE_TARGET | Out-Null"],
                                        env={**self.env, "RRULE_LINK": str(link), "RRULE_TARGET": str(outside)},
                                        capture_output=True, timeout=20)
                self.assertEqual(create.returncode, 0, create.stderr)
                # Use both entrypoints; the wrapper must reject before looking up its helper.
                for helper in self.helpers:
                    result = subprocess.run(["powershell", "-NoProfile", "-File", str(helper),
                                             "-DelaySeconds", "10", "-AutomationId", "audit", "-Apply"],
                                            env={**self.env, "USERPROFILE": str(profile)}, capture_output=True, timeout=20)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b"Linked automation path", result.stderr)
                    self.assertEqual(target.read_bytes(), self.original)

    def test_hardlinked_toml_rejected(self):
        outside = self.profile / "outside.toml"
        os.link(self.target, outside)
        for helper in self.helpers:
            with self.subTest(helper=helper):
                result = self.invoke(helper, "-DelaySeconds", "10", "-AutomationId", "audit-job_1.2", "-Apply")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b"Linked automation path", result.stderr)
                self.assertEqual(outside.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
