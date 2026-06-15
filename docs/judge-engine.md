# 룰 엔진 (`app/judge/`) — 핵심 불변 규칙

> `CLAUDE.md` 에서 `@docs/judge-engine.md` 로 로드됨.

- `judge(case, rider)` 는 **DB·LLM 접근이 없는 순수 함수**. 탐색(F-02)·비교(F-03)는 반드시 이 함수만 호출하고 판정 로직을 중복 구현하지 않는다.
- 판정 우선순위: `waiting_period → boundary → eligible`.
- 분기: `rider.claim_rule is None` → 정액 보장(`boundaries.py::judge_fixed`) / `not None` → 실손(`claim_rule.py::judge_reimbursement`).
- **이중차감 금지**: 실손 `claim_rule.formula` 를 그대로 신뢰하고 비율·공제를 추가로 곱·차감하지 않는다.
- `deductible.type` 이 `by_table`/`from_policy` 면 계산을 보류(`calc=None`).
- 입출력 타입은 `app/judge/types.py`(TypedDict), 상태값은 `app/core/constants.py::JudgeStatus`.

## 테스트 / 정확도 기준

- 룰 엔진 계약 테스트는 `backend/tests/test_judge.py` — 반환 구조(계약)·`claim_rule` 분기·`waiting_period` 우선순위를 고정한다 (DB/LLM 불필요한 순수 함수 테스트).
- 판정·탐색 변경 시 `tests/golden/` 골든셋의 정탐(`expected`)과 오탐(`must_not_match`)을 함께 검증한다. 케이스 스키마는 `tests/golden/README.md`, 채점 러너는 `scripts/eval_golden.py`.
