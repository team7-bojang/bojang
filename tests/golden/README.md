# 골든 정답셋 v2

최종 시나리오 12건(CASE 2 5건 + CASE 1 7건)을 실제 Supabase 특약명과 파싱 조건에 맞춘 자동평가용 JSON입니다.

## 파일

- `cases/*.json`: 기존 `eval_golden.py` 방식처럼 1파일 1케이스
- `golden_set_v2.json`: 12건 합본
- `rider_catalog.json`: 기대 결과에서 참조하는 실제 파싱 특약 스냅샷
- `policy_amount_summary.json`: 12개 시나리오의 보험별 최종 예상보험금만 모은 요약
- `calculation_guide.json`: 특약별 입력값·약관 기준·공제·감액·최종금액 계산 단계
- `schema.json`: 필수 필드·status·금액 계산 규칙
- `FIELD_GUIDE.md`: 시나리오·기대 결과·특약 스냅샷의 전체 필드 설명
- `validate_golden_v2.py`: JSON과 계산값 정적 검증
- `eval_golden_v2.py`: 백엔드 결과와 비교할 때 사용할 평가기 템플릿

## 예상금액 규칙

`estimated_amount`는 약관에서 추출한 지급 산식·비율·공제일수·감액률에
`demo_assumptions`의 보험가입금액 또는 병원비를 대입해 계산한 테스트 예상보험금입니다.
화면에는 `약관 산식 + 데모 입력값 기준 예상보험금`과 심사 안내 문구를 함께 표시합니다.

46개 기대 결과 모두 `estimated_amount` 필드를 가지며, 지급 가능 결과에는 계산된 데모 금액,
면책·조건 미충족·적용 대상 아님 결과에는 `0`이 들어 있습니다.

각 결과의 `amount_basis`에서 약관상 산정 기준과 조항·페이지, 계산에 사용한 데모 입력값을 확인할 수 있습니다.
`policy_amount_summary`에는 보험별 예상보험금 합계가 있으며, CASE2는 비교 입원일수별 합계를 제공합니다.
`calculation_steps`에는 계산 과정을 순서대로 기록하고, 보험별 `total_calculation`에는 특약 금액 합산식을 기록합니다.

감액 대상은 `eligible_reduced`를 사용하지 않고 `status=eligible`과 `reduction.applied=true`로 표현합니다.
가입기간을 구간으로 받는 면책 사례는 정확한 잔여일수 `gap_days`를 표시하지 않습니다.
