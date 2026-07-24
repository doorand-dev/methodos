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
    def test_rejects_mechanical_defects(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            slices:
              - id: 1
                scope_authority: confirmed
                line_budget: 10
                public_contracts: [render]
                files:
                  modify: [src/public.py]
                  test: [tests/test_public.py]
                verification:
                  scope: focused
                  type: unit_test
                  command: test -f tests/test_public.py
                  proves: [A1]
                  risk_predicate: null
                  approved_by: null
                  expected_exit_code: 0
                review_checkpoint: skip
                checkpoint_reason: null
              - id: 1
                scope_authority: confirmed
                line_budget: 10
                files:
                  modify: [src/public.py]
                  test: [tests/test_public.py]
                verification:
                  scope: focused
                  type: unit_test
                  command: pytest tests/test_public.py -v
                  proves: [A1]
                  risk_predicate: null
                  approved_by: null
                  expected_exit_code: 0
                review_checkpoint: skip
                checkpoint_reason: null
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

    def test_accepts_a_scoped_plan(self) -> None:
        result = run_preflight(
            """
            ---
            slug: repair-plan
            status: approved
            slices:
              - id: 1
                scope_authority: confirmed
                line_budget: 80
                files:
                  modify: [src/repair.py]
                  test: [tests/test_repair.py]
                verification:
                  scope: focused
                  type: unit_test
                  command: pytest tests/test_repair.py -v
                  proves: [A1]
                  risk_predicate: null
                  approved_by: null
                  expected_exit_code: 0
                public_callers: []
                review_checkpoint: skip
                checkpoint_reason: null
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
                scope_authority: confirmed
                line_budget: 20
                files:
                  modify: [../outside.py]
                verification:
                  scope: focused
                  type: command
                  command: py -3 repair.py
                  proves: [A1]
                  risk_predicate: null
                  approved_by: null
                  expected_exit_code: 0
                public_callers: []
                review_checkpoint: skip
                checkpoint_reason: null
            ---
            """
            result = run_preflight(plan, root)

        self.assertEqual(result.returncode, 1)
        self.assertIn("declared path escapes --repo", result.stdout)

    def test_rejects_unapproved_scope_and_broad_verification(self) -> None:
        result = run_preflight(
            """
            ---
            slug: excessive-verification
            status: approved
            slices:
              - id: 1
                scope_authority: approved_unresolved
                line_budget: 20
                files:
                  modify: [src/repair.py]
                  test: []
                verification:
                  scope: integration
                  type: command
                  proves: [A1]
                  risk_predicate: null
                  approved_by: null
                public_callers: []
                review_checkpoint: required
                checkpoint_reason: null
            ---
            """
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid or missing scope_authority", result.stdout)
        self.assertIn("broader verification requires a named risk", result.stdout)
        self.assertIn("broader verification requires approval", result.stdout)
        self.assertIn("candidate or required review needs checkpoint_reason", result.stdout)
        self.assertIn("verification command is required", result.stdout)
        self.assertIn("numeric expected_exit_code is required", result.stdout)

    def test_accepts_approved_integration_and_review_candidate(self) -> None:
        result = run_preflight(
            """
            ---
            slug: seam-verification
            status: approved
            slices:
              - id: 1
                scope_authority: user_approved_unresolved
                line_budget: 20
                files:
                  modify: [src/producer.py, src/consumer.py]
                  test: []
                verification:
                  scope: integration
                  type: command
                  command: py -3 verify_seam.py
                  proves: [A1, A2]
                  risk_predicate: changed_producer_consumer_seam
                  approved_by: lifecycle_owner
                  expected_exit_code: 0
                public_callers: []
                review_checkpoint: candidate
                checkpoint_reason: public_contract_if_changed
            ---
            """
        )

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
