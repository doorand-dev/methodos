"""Deterministic contract/eval checks for scoped final implementation review."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def commit(repo: Path, message: str, path: str, content: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    git(repo, "add", "--", path)
    git(
        repo,
        "-c",
        "user.name=scope-test",
        "-c",
        "user.email=scope-test@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git(repo, "rev-parse", "HEAD")


def commit_paths(repo: Path, sha: str) -> set[str]:
    return set(git(repo, "diff", "--name-only", f"{sha}^..{sha}").splitlines())


def owned_paths(repo: Path, owned_commit_shas: list[str]) -> set[str]:
    paths: set[str] = set()
    for sha in owned_commit_shas:
        paths.update(commit_paths(repo, sha))
    return paths


def external_overlap(
    repo: Path,
    provenance_sha: str,
    candidate_sha: str,
    owned_commit_shas: list[str],
    declared_paths: set[str],
) -> set[str]:
    owned = set(owned_commit_shas)
    overlap: set[str] = set()
    for sha in git(repo, "rev-list", "--reverse", f"{provenance_sha}..{candidate_sha}").splitlines():
        if sha not in owned:
            overlap.update(commit_paths(repo, sha) & declared_paths)
    return overlap


class ImplNovelistScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        git(self.repo, "init", "-q")
        self.provenance = commit(self.repo, "approved provenance", "README.md", "approved\n")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_single_owned_commit_ignores_non_overlapping_interleaving(self) -> None:
        foreign = commit(self.repo, "foreign docs", "docs/foreign.md", "foreign\n")
        owned = commit(self.repo, "owned implementation", "src/app.py", "owned\n")

        self.assertIn("docs/foreign.md", commit_paths(self.repo, foreign))
        self.assertEqual(owned_paths(self.repo, [owned]), {"src/app.py"})
        self.assertEqual(
            external_overlap(
                self.repo,
                self.provenance,
                owned,
                [owned],
                {"src/app.py"},
            ),
            set(),
        )

    def test_multiple_owned_commits_ignore_non_overlapping_interleaving(self) -> None:
        first_owned = commit(self.repo, "owned implementation one", "src/app.py", "one\n")
        commit(self.repo, "foreign docs between owned commits", "docs/foreign.md", "foreign\n")
        second_owned = commit(self.repo, "owned implementation two", "tests/test_app.py", "two\n")

        self.assertEqual(
            owned_paths(self.repo, [first_owned, second_owned]),
            {"src/app.py", "tests/test_app.py"},
        )
        self.assertEqual(
            external_overlap(
                self.repo,
                self.provenance,
                second_owned,
                [first_owned, second_owned],
                {"src/app.py", "tests/test_app.py"},
            ),
            set(),
        )

    def test_external_commit_overlapping_declared_path_blocks(self) -> None:
        first_owned = commit(self.repo, "owned implementation one", "src/app.py", "one\n")
        commit(self.repo, "foreign contract overlap", "src/app.py", "foreign\n")
        second_owned = commit(self.repo, "owned implementation two", "tests/test_app.py", "two\n")

        self.assertEqual(
            external_overlap(
                self.repo,
                self.provenance,
                second_owned,
                [first_owned, second_owned],
                {"src/app.py", "tests/test_app.py"},
            ),
            {"src/app.py"},
        )

    def test_approved_revision_is_not_the_final_diff_base(self) -> None:
        commit(self.repo, "foreign docs", "docs/foreign.md", "foreign\n")
        owned = commit(self.repo, "owned implementation", "src/app.py", "owned\n")

        provenance_range = set(
            git(self.repo, "diff", "--name-only", f"{self.provenance}..{owned}").splitlines()
        )
        self.assertEqual(owned_paths(self.repo, [owned]), {"src/app.py"})
        self.assertIn("docs/foreign.md", provenance_range)
        self.assertNotEqual(provenance_range, owned_paths(self.repo, [owned]))

    def test_youtube_incident_fixture_uses_owned_commit_boundary(self) -> None:
        repo = Path(r"C:\youtube-edit-auto")
        if not repo.exists():
            self.skipTest("incident repository is not available")

        provenance = "299406574bae44e1b7560bf9b9a929dbe574cb85"
        foreign = "a15714802d4dbe7e535ab86817bb45a3b56379e8"
        owned = "b4fb349e9467eb832782a07db2777f6376e7246b"
        declared_paths = {
            ".claude/plans/longform-highlight-final-edit-ux.md",
            "dashboard/static/final-edit.css",
            "dashboard/static/final-edit.js",
            "docs/adr/0027-why-longform-capcut-single-save-boundary.md",
            "docs/specs/longform-highlight-final-edit-ux.md",
            "tests/js/test_final_edit_p4.mjs",
        }
        foreign_paths = {
            ".claude/verify-reports/narrative-mic-reveal-order-translation-final-attempt-1.json",
            "docs/ai_step_reference.md",
            "docs/data_flow.md",
            "docs/pipeline.md",
        }

        self.assertEqual(commit_paths(repo, foreign), foreign_paths)
        self.assertEqual(owned_paths(repo, [owned]), declared_paths)
        self.assertEqual(
            external_overlap(repo, provenance, owned, [owned], declared_paths),
            set(),
        )
        provenance_range = set(
            git(repo, "diff", "--name-only", f"{provenance}..{owned}").splitlines()
        )
        self.assertEqual(provenance_range, declared_paths | foreign_paths)

    def test_codex_contract_and_low_risk_routing_are_explicit(self) -> None:
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")
        novelist = (ROOT / "skills/codex/impl-novelist/SKILL.md").read_text(encoding="utf-8")
        using = (ROOT / "skills/codex/using-methodos/SKILL.md").read_text(encoding="utf-8")
        grill = (ROOT / "skills/codex/grill-me/SKILL.md").read_text(encoding="utf-8")
        plan = (ROOT / "skills/codex/plan/SKILL.md").read_text(encoding="utf-8")
        decision = (ROOT / "skills/codex/decision/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("owned_commit_shas", contract)
        self.assertIn("approved_plan_revision", contract)
        self.assertIn("provenance", contract.lower())
        self.assertIn("owned_commit_shas", novelist)
        self.assertNotIn("base..candidate diff", novelist)
        self.assertIn("execution packet", impl.lower())
        self.assertIn("git diff --name-only <sha>^ <sha>", impl)
        self.assertNotIn("git diff --name-only <parent_sha> <commit_sha>", impl)
        self.assertIn("existing", using.lower())
        self.assertIn("user-visible flow", using.lower())
        self.assertIn("final_review_required=true", using)
        self.assertIn("existing", grill.lower())
        self.assertIn("user-visible flow", grill.lower())
        self.assertIn("execution packet", plan.lower())
        self.assertIn("Hard to reverse", decision)
        self.assertIn("WHY", decision)

    def test_high_risk_and_evidence_requirements_remain(self) -> None:
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")

        for marker in (
            "schema or explicit public contract",
            "authority, permission, secret, or security",
            "migration or external state",
            "fresh evidence",
            "terminal regression",
        ):
            self.assertIn(marker, impl + contract)


if __name__ == "__main__":
    unittest.main()
