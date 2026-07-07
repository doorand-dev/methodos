# Methodos Codex 대응 메모

Methodos의 공유 단위는 `SKILL-ARTIFACTS.md` 계약이다. Codex 쪽 자산은 Claude
설치기를 포팅하지 않고, 필요한 배선만 Codex 관습에 맞게 다시 만든다.

- `../../hooks/common/evidence_check.py`: Codex hook으로 재사용 가능한 후보.
- `../../hooks/claude/delegation-enforcer.py`: Claude Agent `.md` frontmatter의 `model:` 전용 훅. Codex에는 그대로 쓰지 않는다.
- `../../hooks/codex/codex-spawn-model-gate.py`: Codex `spawn_agent` 호출에서 모델 선택을 명시하도록 강제하는 후보.
- `../../agents/claude/*.md`: Codex agent `.toml`로 재작성할 후보. 아직 repo 정본 `.toml`은 없다.
- `SKILL.codex.md`: Claude prose를 따르면 실제로 실패하는 절차 차이가 생길 때만 만든다.
