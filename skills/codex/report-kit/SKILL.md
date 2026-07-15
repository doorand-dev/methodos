---
name: report-kit
description: |
  Lifecycle HTML template kit — a shared palette, components, and archetypes for visualizing project progress, data flow, measurement, and verdicts as a single self-contained HTML page. 7 archetypes (spec review, scenario flow, system panorama, lifecycle matrix, measurement snapshot, control A/B diff, verdict form) in 3 families. Explicit trigger-oriented (no over-firing): "/report-kit", "report-kit", "이 키트로", "이 양식으로 만들어", "생애주기 HTML". Consult when newly building one of these forms — do not reinvent the CSS each time. prototype v0.
---

# report-kit (prototype v0)

프로젝트 상태·데이터흐름·측정·판정을 **자기완결 단일 HTML 한 장**으로 시각화하는 공유 키트.
5개 정본 산출물(Poncou·youtube-edit)에서 추출한 시각 DNA를 재사용해, 매번 CSS를 재발명하지
않고 *한 가족으로 보이는* 양식을 빠르게 찍는다.

> **STATUS: prototype v0 — 진화 전제.** 실사용 마찰을 쌓아 evolve. 정합되면 정식 ceremony
> (CONV-GRAPH 한 줄·grep anchor·ASSET-LAYERS 등록 재확인) 부착. 지금은 *쓰면서 배운다* — 보류.

**레퍼런스 = 복붙 출처: [kit.html](kit.html)** — 브라우저로 열어 보고, 거기서 `:root` 팔레트
블록 + 필요한 컴포넌트 마크업을 복사한다. 9 컴포넌트가 실데이터로 렌더돼 있음(골격 그대로 가져다 채움).

## 언제 — 7 아키타입 (본체로 3 family)

| family | 아키타입 | 재생성 | 예시 정본 |
|---|---|---|---|
| **A · 서사형** (설명·합의 · 손작성 · drift 관리) | Spec 검토 · 시나리오 데이터흐름 | 손작성(LLM) | `spec-manual-data-dashboard` · `source-authority-dataflow` |
| **B · 데이터형** (측정·비교 · 코드생성 · 안 stale) | 시스템 전경 · 생애주기 매트릭스 · 측정 스냅샷 · 통제 A/B diff | 하이브리드~코드생성 | `pipeline-overview` · `자막_생애주기` · `source_bench/report` · `_compare_aligners_294` |
| **C · 루프형** (판정 수집 · 코드생성+인터랙티브) | 청취/판정 확정 폼 | 코드생성 | `build_listen_pack` |

상관: **데이터가 본체면 코드생성(안 stale) · 서사가 본체면 손작성(drift 관리 필요).** 전경·생애주기는
골격 코드 + 판단 셀 손 = 하이브리드. B·C는 빌더가 `data→html`(빌더 스크립트가 정본, HTML은 산출).

## 워크플로

1. **아키타입 고름** — 위 표에서 *본체*(설명/측정/판정)로.
2. **kit.html에서 복붙** — `:root` 팔레트 + 해당 아키타입 컴포넌트 마크업.
3. **실데이터로 채움** — 추측 금지, 근거 있는 값만. (못 채우는 건 `pending-note`로 정직하게.)
4. **provenance 푸터 필수** — `생성일 · 정본 file · 근거`. 손작성(A형)이면 "변경 시 손수 갱신" 명시.
5. **자기완결 단일 파일** — CSS 인라인, 증거는 base64 임베드. 서버 0 (OneDrive `share_ai/`에서 그대로 열림).

## 규약 (확정)

- **단일 라이트 테마.** 축 구분은 테마 아닌 **좌측 스트라이프**: 보라=작업물(A, 작업과 함께 졸업) / 파랑=reference(B, 영속).
- **9 컴포넌트**: flow-diagram · cascade-ladder · stage-matrix · case-card · diff-table · verdict-card · stat-cards · pending-note · provenance-footer. (kit.html에 실렌더)
- **OneDrive 공유 (share_ai 정본)**: AI 산출물은 OneDrive 루트 말고 **프로젝트별 폴더** `OneDrive - KIAS/share_ai/<프로젝트>/`에, 파일명 `<설명>-<날짜>.html` (폴더 없으면 만들어 그 안에). 루트·플랫이 난잡해져 사용자가 못 찾는 것 방지. Codex는 최종 응답에 HTML 절대경로를 병기한다.

## Codex·외부 실행자 위임

데이터형(B)·루프형(C)은 빌더라 Codex 적합(기계적·명확스펙). Codex는 같은 PC에서 직접 돌리므로
임베드 프롬프트 말고 **이 스킬 경로를 주고 읽게** 한다 — `~/.agents/skills/report-kit/`의
`SKILL.md`(규약·아키타입)+`kit.html`(`:root` 팔레트 + 9 컴포넌트 복붙 출처). 서사형(A)은 판단이 커 직접 작성 권장.

## 방법론은 여기 말고 (경계)

키트는 *표시*만 한다. 두 규율은 템플릿이 아니라 별도 산다:

- **통제변수 비교법** (같은 입력 · prod 경로 통과 · try/finally 상태 원복 · 요약통계) — `finding`/체크리스트로. 통제 A/B diff 양식의 본질 70%가 이 규율이고 HTML은 30%다. 표시만 키트에서.
- **provenance 갱신 규율** (A형 손작성 drift 방어) — `provenance-footer` 규약 + 갱신일로.

## evolve (v0 → 정합)

실사용 마찰을 누적하다 정합 판단이 서면: CONV-GRAPH 한 줄 + (영속 doc-producer로 굳으면) grep
anchor 선언 + ASSET-LAYERS 분류 재확인 후 전역 인스턴스 drift-sync 점검. 빌더 패턴 2종(B형
`data→html`, C형 round-trip)을 재사용 스크립트로 추출하는 것도 evolve 후보.
