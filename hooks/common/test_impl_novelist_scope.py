"""Small deterministic checks for the shared implementation contract."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contract/SKILL-ARTIFACTS.md"

HIGH_RISK_PREDICATES = {
    "schema_or_public_contract",
    "authority_or_security",
    "persistence_or_idempotency",
    "migration_or_external_state",
    "financial_execution",
    "downstream_foundation",
}


def exact_changed_paths(changed: set[str], declared: set[str]) -> bool:
    """A slice is exact only when its changed paths equal its declaration."""
    return changed == declared


def conditional_review_required(risks: set[str]) -> bool:
    """High-risk review is conditional on an explicit impact predicate."""
    return bool(risks & HIGH_RISK_PREDICATES)


class ImplNovelistScopeTests(unittest.TestCase):
    def test_exact_changed_paths_are_file_count_independent(self) -> None:
        self.assertTrue(
            exact_changed_paths(
                {"src/app.py", "tests/test_app.py"},
                {"src/app.py", "tests/test_app.py"},
            )
        )
        self.assertFalse(
            exact_changed_paths(
                {"src/app.py", "docs/foreign.md"},
                {"src/app.py"},
            )
        )

    def test_high_risk_review_predicates_are_conditional(self) -> None:
        self.assertFalse(conditional_review_required(set()))
        self.assertTrue(conditional_review_required({"authority_or_security"}))
        self.assertTrue(conditional_review_required({"migration_or_external_state"}))
        self.assertFalse(conditional_review_required({"ordinary_refactor"}))

    def test_shared_contract_keeps_operational_safety(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8")
        for marker in (
            "exact paths",
            "verification",
            "user approval",
            "public_callers",
            "changed-path",
            "caller / producer / consumer / failure",
        ):
            self.assertIn(marker, contract)

    def test_shared_contract_has_no_runtime_attestation_ceremony(self) -> None:
        contract = CONTRACT.read_text(encoding="utf-8").lower()
        for marker in (
            "source_spec.sha",
            "approved_plan_revision",
            "owned_commit_shas",
            "reviewed_candidate_sha",
            "owner_thread_or_session",
            "sdd-terminal-report",
            "impl-worker-report",
            "artifact_sha256",
            "session identity",
            "model/effort",
            "why commit",
        ):
            self.assertNotIn(marker.lower(), contract)


if __name__ == "__main__":
    unittest.main()
