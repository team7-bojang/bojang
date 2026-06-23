# judge 룰테이블 연동 — 핸드오프 메모

judge 는 순수 함수로서 **집합 매칭 인터페이스**까지 구현 완료. 아래는 judge 밖(타 도메인)에서
채워줘야 production 에서 동작하는 항목들의 명세다. (golden v2-2 기준 8/12·43/47 통과)

## judge 가 새로 받는 입력 (계약 — 이미 구현됨)

`Case` 에 resolver 가 채워줄 필드:
- `disease_groups: list[str]` — 이 질병(KCD)이 속한 질병군 id (예: 갑상선암 → `["thyroid_cancer","similar_cancer","cancer_all"]`)
- `treatment_codes: list[str]` — 표준화된 치료항목 코드 (예: `["XRAY","CAST"]`)
- `covered_amounts` — 실손 특약별 보상대상 의료비 (급여/비급여 분리)

`Rider` 에 resolver 가 채워줄 필드:
- `require_groups` / `exclude_groups` — 요구/제외 질병군 (`rider_disease_rules`)
- `require_treatments` — 요구 치료항목 코드 (`rider_treatment_rules`)

→ 이 필드가 있으면 judge 는 집합 매칭으로 판정하고, 없으면 기존 키워드 휴리스틱으로 폴백한다.

## ① 조윤 (서비스) — resolver 를 `analysis_service.py` 에 구현

동작 검증된 참조 구현이 **`scripts/score_golden_v2.py` 의 `Resolver` 클래스**에 있다
(`python scripts/score_golden_v2.py <golden.json>` 로 재현 가능). 4개 룰테이블을 읽어 위 필드를 채운다:
- KCD → 질병군: `disease_group_code_rules` (include/exclude 범위 매칭)
- 특약명 패턴 → 요구/제외 질병군: `rider_disease_rules` (LIKE + `require_trigger_type`)
- 치료항목 alias → 코드: `treatment_types.aliases`
- rider_id → 요구 치료코드: `rider_treatment_rules`
- 실손 covered_amount(급여/비급여)·정액 coverage_amount 는 챗봇/입력에서 특약별로 전달

## ② 진미경 (약관/질병군 데이터) — 수정 2건

1. **암진단자금 매핑 (골든 c1_01·c2_04 실패 원인)**
   - 현재 `rider_disease_rules` 의 `%암진단%` → `cancer_all` 인데, `cancer_all` 은 C73(갑상선암) 포함.
   - 일반 "암진단자금"은 **유사암 제외**가 정답(`general_cancer_excl_similar` 는 C44/C73/D00-09/D37-48 제외).
   - → 유사암제외 표기 없는 일반 암진단비/진단자금이 `general_cancer_excl_similar` 를 요구하도록 규칙 보강 필요.

2. **중복 rider (골든 c1_04 실패 원인)**
   - "갱신형 상해MRI/CT검사비(급여,연간1회한)보장 특별약관" 이 메리츠에 **2건 중복**(`eb74f305…`, `29749d86…`).
   - 한쪽만 `rider_treatment_rules`(CT required)에 매핑됨 → 중복 제거 또는 양쪽 매핑.

## 참고 — 데이터/judge 아님

- **골절진단비Ⅱ (골든 c1_03)** 는 골든 정답셋이 `note: "별도 확인 대상으로 유지"` 로 **의도적 보류**.
  무리하게 맞추면 c1_04 의 동일 특약(eligible)이 깨진다. → 손대지 않음.
