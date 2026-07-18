"""Regression checks for the deterministic plan-review preflight."""

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("plan_preflight.py")


def run_preflight(plan: str, repo: Path | None = None) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "plan.md"
        path.write_text(textwrap.dedent(plan).lstrip(), encoding="utf-8")
        command = [sys.executable, str(SCRIPT), str(path)]
        if repo is not None:
            command.extend(["--repo", str(repo)])
        return subprocess.run(command, text=True, capture_output=True, check=False)


class PlanPreflightTests(unittest.TestCase):
    def test_rejects_mechanical_defects_without_sha_requirements(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            slices:
              - id: 1
                line_budget: 10
                public_contracts: [render]
                files:
                  modify: [src/public.py]
                  test: [tests/test_public.py]
                verification:
                  type: unit_test
                  command: test -f tests/test_public.py
                  expected_exit_code: 0
              - id: 1
                line_budget: 10
                files:
                  modify: [src/public.py]
                  test: [tests/test_public.py]
                verification:
                  type: unit_test
                  command: pytest tests/test_public.py -v
                  expected_exit_code: 0
            ---

            ### Slice 1: repair
            TBD
            """
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate slice id: 1", result.stdout)
        self.assertIn("path owned by multiple slices: src/public.py", result.stdout)
        self.assertIn("POSIX shell syntax", result.stdout)
        self.assertIn("placeholder", result.stdout)
        self.assertIn("public_contracts requires public_callers inventory", result.stdout)
        self.assertNotIn("source_spec.sha", result.stdout)

    def test_accepts_a_sha_less_scoped_plan(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            slices:
              - id: 1
                line_budget: 80
                files:
                  modify: [src/repair.py]
                  test: [tests/test_repair.py]
                verification:
                  type: unit_test
                  command: pytest tests/test_repair.py -v
                  expected_exit_code: 0
                public_callers: []
            ---

            ### Slice 1: repair
            """
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_rejects_declared_path_outside_repo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            root.mkdir()
            plan = """
            ---
            slug: boundary-plan
            status: approved
            slices:
              - id: 1
                line_budget: 20
                files:
                  modify: [../outside.py]
                verification:
                  type: command
                  command: py -3 repair.py
                  expected_exit_code: 0
                public_callers: []
            ---
            """
            result = run_preflight(plan, root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("declared path escapes --repo", result.stdout)


if __name__ == "__main__":
    unittest.main()
