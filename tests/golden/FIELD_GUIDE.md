# 골든 정답셋 v2 필드 설명서

JSON은 `// 주석`을 허용하지 않으므로, 데이터 파일을 깨뜨리지 않도록 컬럼 설명을 이 문서에 분리했습니다.

## 예상 보험금 표기

- 46개 `expected` 결과 모두 `estimated_amount`가 있습니다.
- 지급 가능 결과 32개에는 데모 가입금액으로 계산한 예상금액이 들어 있습니다.
- 면책, 조건 미충족, 적용 대상 아님에 해당하는 14개 결과는 `0`입니다.
- 지급 산식·비율·공제일수·감액률은 약관에서 가져옵니다.
- 보험가입금액과 병원비는 실제 사용자 자료 대신 데모 입력값을 사용합니다.
- 따라서 결과 화면 계산을 검증할 수 있지만 보험사의 확정 보험금으로 사용하면 안 됩니다.

## 시나리오 최상위 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `schema_version` | string | 골든셋 구조 버전입니다. |
| `id` | string | 시나리오 고유 ID입니다. 예: `c2_01`. |
| `service_type` | string | `CASE1`은 보장 탐색, `CASE2`는 조건 비교 시나리오입니다. |
| `description` | string | 시나리오를 한 줄로 설명합니다. |
| `selected_policies` | string[] | 분석 대상으로 선택한 보험 상품명입니다. |
| `case` | object | 사용자가 입력하거나 챗봇 질문으로 수집한 상황 정보입니다. |
| `demo_assumptions` | object | 예상금액 계산에 사용하는 임시 가입금액입니다. |
| `expected` | object[] | 백엔드가 반환해야 하는 특약별 정답 결과입니다. |
| `must_not_match` | object[] | 검색 결과에 나타나면 오탐으로 처리할 특약입니다. |
| `expected_summary` | object | 기대 결과 개수나 빈 결과 여부를 요약합니다. |
| `display_rule` | object | 프론트 화면의 금액 라벨과 안내 문구 규칙입니다. |
| `demo_amount_inputs` | object[] | 계산에 대입한 데모 보험가입금액·병원비와 입력값 출처입니다. |
| `policy_amount_summary` | object[] | 보험별 최종 예상보험금 합계입니다. CASE2는 비교 일수별로 나뉩니다. |
| `comparison_basis` | string | CASE2의 비교 기준입니다. 입원일수, 가입기간, 복합 조건 등을 나타냅니다. |

## `case` 사용자 상황 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `initial_situation` | string | 사용자가 처음 입력한 자연어 상황입니다. |
| `disease` | string | 사용자에게 확인된 질병명입니다. |
| `disease_kcd` | string | 질병과 매핑된 KCD 코드입니다. |
| `is_inpatient` | boolean | 입원 치료 여부입니다. |
| `is_outpatient` | boolean | 통원 치료 여부입니다. |
| `surgery` | boolean | 수술 여부입니다. |
| `admission_days_current` | integer/null | 현재까지 실제 입원한 일수입니다. |
| `admission_days_diagnosed` | integer/null | 의사 권고 또는 진단서상 예정 입원일수입니다. |
| `treatment_items` | string[] | MRI, CT, 주사, 깁스 등 표준 치료코드 목록입니다. |
| `annual_visit_count` | integer | 동일 치료의 연간 횟수 조건을 판단하기 위한 값입니다. |
| `visit_dates` | string[] | 연간 횟수나 재방문 간격을 판단할 때 사용하는 진료일 목록입니다. |
| `payment_amount` | integer | 결제내역 기반 시나리오에서 확인된 병원 결제금액입니다. |
| `policy_elapsed_days` | integer | 보험 가입 후 경과일입니다. 면책·감액 판단에 사용합니다. |
| `contract_type` | string | 갱신형 또는 비갱신형 구분입니다. 감액 조건에 필요할 수 있습니다. |
| `age` | integer | 연령 조건이 있는 감액 규칙을 판단할 때 사용합니다. |

## `demo_assumptions` 금액 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `coverage_amount` | integer | 진단비·수술비처럼 한 번 지급되는 정액형 보장의 임시 가입금액입니다. |
| `coverage_amount_per_day` | integer | 입원일당의 임시 1일 가입금액입니다. |
| `covered_amount` | integer | 실손 계산에 사용하는 데모 급여·비급여 대상 의료비입니다. |

`demo_assumptions`의 금액은 실제 Supabase 가입금액이 아닙니다. 현재 Supabase 특약 대부분은 `unit_amount`가 비어 있으므로 화면 시연과 계산 검증을 위해 임시로 넣은 값입니다.

## `expected` 기대 결과 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `policy` | string | 정답으로 기대하는 보험 상품명입니다. |
| `rider` | string | 정답으로 기대하는 특약명입니다. |
| `rider_catalog_key` | string | `rider_catalog.json`에서 근거 특약을 찾는 키입니다. |
| `status` | string | 룰엔진의 기대 판정 상태입니다. |
| `estimated_amount` | integer | 데모 가입금액 기준 예상금액입니다. 지급 대상이 아니면 `0`입니다. |
| `calculation` | string/null | 예상금액 계산식을 사람이 읽을 수 있게 적은 값입니다. |
| `scenario_days` | integer | 입원 3일과 7일처럼 비교 중인 해당 결과의 기준 일수입니다. |
| `payable_days` | integer | 최소 입원일수와 공제일수를 반영한 실제 계산 대상 일수입니다. |
| `gap_days` | integer | 지급 조건까지 부족한 일수입니다. 가입기간을 구간으로 받은 면책 사례에는 표시하지 않습니다. |
| `reduction` | object | 가입 초기 감액 적용 정보입니다. |
| `note` | string | 적용 또는 미적용 이유를 보충 설명합니다. |
| `amount_basis` | object | 약관상 금액 산식, 계산에 사용한 데모 입력값, 근거 조항과 페이지입니다. |
| `calculation_steps` | object[] | 입력값부터 약관 기준, 지급일수, 감액, 최종금액까지의 순서별 계산 과정입니다. |

### `amount_basis` 금액 근거 필드

| 필드 | 의미 |
|---|---|
| `coverage_kind` | 정액형 또는 실손형 구분 |
| `policy_rule` | 약관에서 추출한 보험금 산정 기준 |
| `claim_formula` | 실손처럼 약관에 계산식이 있는 경우의 구조화 산식 |
| `demo_input` | 계산에 대입한 데모 보험가입금액 또는 데모 병원비 |
| `policy_source` | 산식 근거가 되는 약관 조항과 페이지 |
| `result_meaning` | 해당 금액이 계산된 방식 또는 0원인 이유 |

## `policy_amount_summary` 보험별 금액

| 필드 | 의미 |
|---|---|
| `policy` | 보험 상품명 |
| `scenario_days` | CASE2 입원일수 비교에서 해당 합계의 기준 일수 |
| `estimated_amount` | 해당 보험에서 받을 수 있는 특약 예상금액 합계 |
| `amount_label` | 화면 표시용 금액 성격 |
| `note` | 지급 가능 특약이 없는 경우 등의 설명 |
| `calculation_breakdown` | 보험별 합계에 포함된 특약명·개별 계산식·금액 |
| `total_calculation` | 특약별 금액을 더해 보험별 합계를 만든 산식 |

### `status` 값

| 값 | 의미 |
|---|---|
| `eligible` | 현재 입력 조건상 지급 가능 후보입니다. |
| `claimed` | 이미 청구한 보장입니다. |
| `boundary_not_met` | 최소 입원일수 등 지급 경계조건을 충족하지 못했습니다. |
| `waiting_period_not_met` | 면책기간이 지나지 않았습니다. |
| `verification_required` | 추가 서류나 정보 확인이 필요합니다. |
| `not_applicable` | 질병·치료·보장 조건상 적용 대상이 아닙니다. |
| `potential` | 가능성은 있으나 확정 판단에 정보가 부족합니다. |

### `reduction` 감액 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `applied` | boolean | 감액 적용 여부입니다. |
| `rate` | number | 실제 지급 비율입니다. `0.5`는 50% 지급입니다. |
| `until_elapsed_days` | integer | 이 경과일까지 감액 조건이 적용된다는 뜻입니다. |

## `must_not_match` 오탐 방지 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `policy` | string | 검색되면 안 되는 특약의 보험 상품명입니다. |
| `rider` | string | 검색되면 안 되는 특약명입니다. |
| `reason` | string | 해당 특약이 오탐인 이유입니다. |

## `expected_summary` 요약 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `eligible_count` | integer | 지급 가능으로 기대하는 결과 수입니다. |
| `not_met_count` | integer | 면책·경계 미충족·적용 불가 등 결과 수입니다. |
| `empty_result` | boolean | 정상적인 기대 결과가 빈 목록인지 표시합니다. |

## `display_rule` 화면 표시 필드

| 필드 | 형식 | 의미 |
|---|---|---|
| `amount_label` | string | 금액 위에 표시할 라벨입니다. |
| `disclaimer` | string | 실제 지급 여부와 금액이 달라질 수 있다는 안내 문구입니다. |
| `show_total_as_confirmed_payment` | boolean | 예상금액 합계를 확정 보험금처럼 표시할지 여부입니다. 항상 `false`입니다. |

## `rider_catalog.json` 특약 스냅샷 필드

| 필드 | 의미 |
|---|---|
| `policy` | 보험 상품명 |
| `name` | 특약명 |
| `is_main` | 주계약 여부 |
| `trigger_type` | 진단·입원·수술 등 지급 발생 유형 |
| `trigger_detail` | 약관상 구체적인 지급 조건 |
| `coverage_kind` | 정액 또는 실손 보장 구분 |
| `unit_amount` | 약관에 명시된 단위 금액. 가입금액에 따라 달라지면 `null` |
| `unit_type` | 1일당, 1회당, 일시금 등 지급 단위 |
| `unit_basis` | 보험가입금액 등 금액 산정 기준 |
| `boundaries` | 최소 입원일수 등 지급 경계조건 |
| `deduct_days` | 계산에서 제외하는 공제일수 |
| `limits` | 1회 입원, 연간, 평생 등의 지급 한도 |
| `waiting_period_days` | 보장개시 전 면책기간 |
| `reductions` | 가입 초기 감액 조건 |
| `exclusions` | 보장하지 않는 사유 |
| `claim_rule` | 실손 계산 등 별도 청구 계산 규칙 |
| `source` | 조항명, 페이지, 약관 원문 |
| `verified` | 파싱 결과 검수 여부 |
