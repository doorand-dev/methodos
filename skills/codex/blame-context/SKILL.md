---
name: blame-context
description: “방금 왜 틀렸는지 고쳐”, blame context·blame-context·컨텍스트 탓해봐처럼 사건 원인 확인을 명시적으로 요청할 때 문맥을 포함한 실제 원인을 판별하고 근거 있는 국소 수정을 즉시 반영한다. 원인 질문·기록만 요청하면 그 범위에 머문다. 스킬의 존재 확인·편집 요청이나 일반적인 정정은 사건 수집을 발동하지 않는다.
---

# Blame Context

현재 세션에 남아 있는 오판·사용자 정정·실제 입력을 근거로 해당 사건을 해결한다. subagent나 새 세션으로 판단을 넘기지 않고 직접 관련된 문맥과 실행 경로만 읽는다.

- 당시 실제로 제공된 지침·파일·훅 출력·라우팅을 재구성한다. 현재 파일이 당시에도 로딩됐다고 가정하지 않는다. 모델 기억을 필수 입력 경로로 취급하지 않는다.
- 원인을 `missing-context`, `stale-context`, `wrong-routing`, `wrong-authority`, `over-context`, `ambiguous-contract`, `model-misread`, `not-context`, `unresolved` 중 근거에 맞게 분류한다. 문맥 탓이 아닌 결과도 보존한다.
- 일반적인 blame 호출은 원인 확인과 해당 기능의 최소 국소 수정을 포함한다. 중복·낡은 지침 삭제, 잘못된 참조·트리거·권한 해석·기존 호출부 수정부터 검토한다. 규칙·훅·검수 단계 추가를 기본 해법으로 삼지 않는다. 실제 원인이 코드나 도구 사용 실수라면 그것을 바로잡고 문맥 규칙으로 덮지 않는다.
- 확인된 원인은 승인된 작업·경로 안에서 바로 고치고 대체된 참조도 정리한다. 원인 질문·기록만·읽기 전용 요청은 수정하지 않는다. 원인이 불확실하면 판별할 최소 확인만 수행하며 추정으로 수정하지 않는다. 다른 프로젝트·외부 효과·권한 변경이나 큰 재설계가 필요하면 근거와 남은 선택을 알린다.
- 해당 오판을 유발한 입력·소비 경로로 수정 효과를 최소 확인한다. 실행하지 못한 범위는 밝히고 완료로 표시하지 않는다. 전체 감사·회귀·독립 검수를 자동으로 붙이지 않는다.

## 사건 기록

`<workspace>/.Codex/context-friction.md`에 사건 발생 시에만 다음 번호의 `CTX-001` 형식으로 짧게 남긴다. 기존 항목과 schema를 유지하며 같은 사건을 처리할 때는 결과를 갱신한다.

```markdown
## CTX-001
- trigger: <실제 사용자 호출>
- misread: <무엇을 무엇으로 오인했는가>
- expected-context: <판단에 필요했던 최소 문맥>
- available-context: <당시 실제 제공된 문맥>
- failed-edge: <입력·계기·소비자·수명·권한 중 문제 경로 또는 unresolved>
- classification: <분류>
- context-fault: yes | no | uncertain
- evidence: <path:line 또는 관찰 결과>
- next-guard: <최소 수정 또는 미해결 확인; 새 guard 추가를 뜻하지 않음>
- status: open | closed | resolved
- resolution: <실제 수정·확인 결과 또는 미실행 이유>
```

확인된 문맥 원인을 수정·검증했으면 `resolved`, 미해결이면 `open`, 문맥 원인이 아니면 `closed`로 둔다. `closed`는 관련 기능 수정 완료를 뜻하지 않는다. 기록만으로 끝내지 않고 실제 변경·확인 범위와 남은 문제를 보고한다.

이번 사건을 넘어 세션의 반복 삽질·도구 낭비를 찾으려면 [retro](../retro/SKILL.md)의 관점을 사용한다. 문맥 정리와 구조 개선은 [improve-context](../improve-context/SKILL.md), 다음 AI의 시작 입력 검토는 [context-novelist](../context-novelist/SKILL.md)가 맡는다. 이미 좁혀진 원인을 다시 조사하거나 사용자에게 후속 스킬 호출을 요구하지 않는다.
