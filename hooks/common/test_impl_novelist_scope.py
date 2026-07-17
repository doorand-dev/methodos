"""Deterministic contract/eval checks for scoped final implementation review."""

from __future__ import annotations

import subprocess
import tempfile
import tomllib
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
        self.assertIn("SDD owner", using)
        self.assertIn("existing", grill.lower())
        self.assertIn("user-visible flow", grill.lower())
        self.assertIn("execution packet", plan.lower())
        self.assertIn("Hard to reverse", decision)
        self.assertIn("WHY", decision)

    def test_sdd_owner_owns_reviewer_dispatch_and_scoped_reuses_thread(self) -> None:
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")
        novelist = (ROOT / "skills/codex/impl-novelist/SKILL.md").read_text(encoding="utf-8")
        checkpoint = (ROOT / "agents/codex/impl-checkpoint-reviewer.toml").read_text(
            encoding="utf-8"
        )
        final = (ROOT / "agents/codex/impl-novelist.toml").read_text(encoding="utf-8")
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")

        self.assertIn("It makes no reviewer call.", impl)
        self.assertIn("SDD owner makes a fresh read-only", impl)
        self.assertIn("reviewer thread/session", impl)
        self.assertIn("same thread/session", novelist)
        self.assertIn("SDD owner calls attempt 1", checkpoint)
        self.assertIn("same reviewer thread", final)
        self.assertIn("reviewer_thread_or_session", contract)
        self.assertIn('"kind": "sdd-terminal-report"', contract)
        self.assertNotIn("impl-novelist-scoped-reviewer", impl + novelist + contract)
        self.assertFalse((ROOT / "agents/codex/impl-novelist-scoped-reviewer.toml").exists())

    def test_impl_routes_delegated_slices_through_luna_agent_profiles(self) -> None:
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")
        high = tomllib.loads(
            (ROOT / "agents/codex/luna-high-worker.toml").read_text(encoding="utf-8")
        )
        maximum = tomllib.loads(
            (ROOT / "agents/codex/luna-max-worker.toml").read_text(encoding="utf-8")
        )
        sdd_owner = tomllib.loads(
            (ROOT / "agents/codex/luna-max-sdd-owner.toml").read_text(encoding="utf-8")
        )

        self.assertIn("fresh custom", impl)
        self.assertIn("`luna-high-worker`", impl)
        self.assertIn("`luna-max-worker`", impl)
        self.assertEqual(high["model"], "gpt-5.6-luna")
        self.assertEqual(high["model_reasoning_effort"], "high")
        self.assertEqual(maximum["model"], "gpt-5.6-luna")
        self.assertEqual(maximum["model_reasoning_effort"], "max")
        self.assertEqual(sdd_owner["model"], "gpt-5.6-luna")
        self.assertEqual(sdd_owner["model_reasoning_effort"], "max")
        self.assertEqual(sdd_owner["agents"]["max_depth"], 2)
        self.assertIn("do not write production implementation", sdd_owner["developer_instructions"])
        self.assertIn("root/project orchestrator owns only", sdd_owner["developer_instructions"])

    def test_local_reviewer_profiles_encode_baseline_and_same_thread_followup(self) -> None:
        checkpoint_profile = tomllib.loads(
            (ROOT / "agents/codex/impl-checkpoint-reviewer.toml").read_text(encoding="utf-8")
        )["developer_instructions"]
        final_profile = tomllib.loads(
            (ROOT / "agents/codex/impl-novelist.toml").read_text(encoding="utf-8")
        )["developer_instructions"]
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")

        for marker in (
            "attempt=1",
            "parent_candidate_sha=null",
            'review_scope="full"',
            "attempt>=2",
            "parent_candidate_sha set to the previous reviewed candidate",
            'review_scope="scoped"',
            "unaffected stage as SKIPPED",
        ):
            self.assertIn(marker, final_profile)

        self.assertIn("reviewer_thread_or_session", checkpoint_profile)
        self.assertIn("reviewer_thread_or_session", final_profile)
        self.assertIn("impl-worker-report`, v1.2", contract)

        checkpoint_schema = contract.split("### impl-checkpoint schema", 1)[1].split(
            "### impl-narrative-final schema", 1
        )[0]
        final_schema = contract.split("### impl-narrative-final schema", 1)[1].split(
            "**Evidence 작성 정본 룰", 1
        )[0]
        self.assertIn('"reviewer_thread_or_session"', checkpoint_schema)
        self.assertIn('"reviewer_thread_or_session"', final_schema)

    def test_required_checkpoint_and_owner_identity_have_no_legacy_codex_route(self) -> None:
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("final_review_required", contract)
        self.assertNotIn("approved_plan.slices.length == 1", contract)
        self.assertIn("Required checkpoint를 final\n  review로 대체하거나 생략하지 않는다.", contract)

        impl_verify_schema = contract.split("### impl-verify schema", 1)[1].split(
            "### impl-checkpoint schema", 1
        )[0]
        self.assertIn("아래 lineage, model/effort 상속", impl_verify_schema)
        self.assertIn("`impl-verify` realization에만 적용", impl_verify_schema)
        self.assertNotIn("Codex 기본 final full route", impl_verify_schema)
        self.assertNotIn("Codex attempt 2+", impl_verify_schema)
        self.assertIn("같은 reviewer thread/session follow-up", contract)
        self.assertNotIn("attempt 2+ scoped는 부모 session model/effort를 상속", contract)
        codex_attempt2_bullets = [
            bullet
            for bullet in contract.split("\n- ")
            if "Codex" in bullet and "attempt 2+" in bullet
        ]
        self.assertTrue(codex_attempt2_bullets)
        for bullet in codex_attempt2_bullets:
            self.assertNotIn("부모 session", bullet)
            self.assertNotIn("inherited_from_parent", bullet)
        self.assertIn("inherited_from_parent", contract)

        worker_schema = contract.split("### Worker handoff schema", 1)[1].split(
            "### Runtime impl advisory schema", 1
        )[0]
        self.assertIn('"owner_thread_or_session"', worker_schema)
        self.assertIn("same `owner_thread_or_session` value", worker_schema)
        self.assertIn("owner_thread_or_session", impl)
        self.assertIn("equal the attempt-1 implementation report", impl)

    def test_luna_high_default_has_evidence_only_max_escalation(self) -> None:
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("`high` by default", impl)
        self.assertIn("demonstrably failed to converge", impl)
        self.assertIn("Multi-slice work, cross-module reach, file", impl)
        self.assertNotIn("multi-slice or cross-module impact", impl)

    def test_high_risk_and_evidence_requirements_remain(self) -> None:
        impl = (ROOT / "skills/codex/impl/SKILL.md").read_text(encoding="utf-8")
        contract = (ROOT / "contract/SKILL-ARTIFACTS.md").read_text(encoding="utf-8")

        for marker in (
            "schema or explicit public contract",
            "authority, permission, secret, or security",
            "migration or external state",
            "fresh evidence",
            "terminal_regression",
        ):
            self.assertIn(marker, impl + contract)


if __name__ == "__main__":
    unittest.main()
