# golden — 평가용 골든 정답셋 (설계서 6-6)

검색·판정 정확도의 **공식 기준**. 진미경(기획 오너)이 약관 원문을 확인하며 20~30개 작성,
이태경이 테스트 코드화·자동 채점기를 구현한다. 조윤의 RAG 튜닝 목표치도 이 채점으로 측정.

`cases/` 아래에 케이스별 JSON 을 둔다. 파일명은 `golden_NN.json` (예: `golden_01.json`).

## 케이스 스키마

```jsonc
{
  "meta": {                           // 케이스 메타 (채점에는 미사용, 추적·검수용)
    "id": "golden_01",                // 파일 기준 식별자
    "title": "시나리오 A — 뇌경색 3일차, 경계 1일 미달",
    "covers_ac": ["AC-02", "AC-03"],  // 이 케이스가 커버하는 인수기준(Acceptance Criteria)
    "verified": false,                // 원문 대조 검수 완료 여부 (사람이 최종 확인 후 true)
    "notes": "원문 검증 근거·페이지·산식 메모 (예: gap_days = condition_days − current_days)"
  },
  "case": {                           // judge() 입력과 동일 형태
    "disease_kcd": "I63",             // 질병 KCD 코드
    "disease_name": "뇌경색증",
    "surgery": false,
    "diag_days": 7,                   // 진단 경과일
    "current_days": 3,                // 현재 입원일수
    "policy_elapsed_days": 800,       // 가입 경과일. null → 면책·감액 "확인 불가"
    "age": 45,                        // (선택) 연령
    "contract_type": "갱신형",         // (선택) 계약 형태
    "registered_policies": ["db_3대질병", "hyundai_실손", "hanwha_e암"],  // 가입 보험 key
    "claimed_policy_keys": ["hyundai_실손"]                              // 이미 청구한 보험 key
  },
  "expected": [                       // 반드시 탐색돼야 하는 보장(정탐) — 누락 시 실패
    {
      "policy": "db_3대질병",
      "rider": "질병입원일당(1일이상180일한도)",
      "status": "eligible",           // 판정 상태 (아래 목록)
      "missed": true,                 // 사용자가 놓친(미청구) 보장인지
      "gap_days": null,               // boundary 미달 시 부족 일수 (예: 4−3=1)
      "calc_struct": "가입금액(1일당) × 3일",   // (선택) 지급액 산식 구조
      "limit_note": "1회 입원당 180일 한도",     // (선택) 한도 메모
      "reduction": null,              // (선택) 감액 조건
      "evidence": {                   // 약관 원문 근거
        "article_no": "질병입원일당 특별약관 1.(보험금의 지급사유)",
        "page": 60
      }
    }
  ],
  "must_not_match": [                 // 잡히면 안 되는 보장(오탐 검증) — 정탐만큼 중요
    {
      "policy": "db_3대질병",
      "rider": "허혈심장질환입원일당(4일이상120일한도)",
      "why": "뇌경색≠허혈심장 — 유사 특약명 오탐 검증(핵심)"
    }
  ]
}
```

- `expected[].status` 값: `eligible / claimed / boundary_not_met / waiting_period_not_met / not_applicable / potential`
  - 이미 청구한 보장은 `claimed`, 경계(예: 4일 이상) 미달은 `boundary_not_met`(+`gap_days`).
- `expected[].evidence` 는 `article_no`·`page` 로 약관 원문 위치를 명시한다 (근거 추적·검수용).
- (선택) 실손 `claim_rule` 검증 케이스는 `expected[].calc_struct` 에 산식 구조를 둔다.
- 검수 원칙: 정액 보장은 `claim_rule=null`, 실손만 작성 / 이중차감 금지.
- `meta.verified` 는 원문 검수 완료 시에만 `true`. 검수 전 케이스는 `false` 유지.

채점 러너: [`../../scripts/eval_golden.py`](../../scripts/eval_golden.py) — `cases/*.json` 을 로드해 파이프라인 연결 후 CI 자동 채점 (`case` 입력 → 결과를 `expected`·`must_not_match` 와 대조).
