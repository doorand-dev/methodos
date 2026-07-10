"""Regression checks for the deterministic plan-review preflight."""

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("plan_preflight.py")


def run_preflight(plan: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "plan.md"
        path.write_text(textwrap.dedent(plan).lstrip(), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path)],
            text=True,
            capture_output=True,
            check=False,
        )


class PlanPreflightTests(unittest.TestCase):
    def test_rejects_mechanical_defects_before_semantic_review(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            source_spec:
              path: docs/specs/repair-plan.md
              sha: deadbeef
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
        self.assertIn("source_spec.sha must be a 40-hex git blob SHA", result.stdout)
        self.assertIn("public_contracts requires public_callers inventory", result.stdout)

    def test_accepts_a_small_scoped_delta(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            source_spec:
              path: docs/specs/repair-plan.md
              sha: 0123456789abcdef0123456789abcdef01234567
            amendment:
              baseline_status: DONE
              scope: [2]
            slices:
              - id: 2
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

            ### Slice 2: repair
            """
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)

    def test_rejects_source_spec_sha_drift_when_repo_is_given(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "docs/specs/repair-plan.md"
            spec.parent.mkdir(parents=True)
            spec.write_text("approved source", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            plan = root / "plan.md"
            plan.write_text(
                textwrap.dedent(
                    """
                    ---
                    slug: repair-plan
                    status: approved
                    source_spec:
                      path: docs/specs/repair-plan.md
                      sha: 0123456789abcdef0123456789abcdef01234567
                    slices:
                      - id: 1
                        line_budget: 20
                        files:
                          modify: [src/repair.py]
                        verification:
                          type: command
                          command: py -3 repair.py
                          expected_exit_code: 0
                        public_callers: []
                    ---
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(plan), "--repo", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("source_spec.sha does not match", result.stdout)


if __name__ == "__main__":
    unittest.main()
