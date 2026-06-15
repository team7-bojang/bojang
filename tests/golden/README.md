# golden — 평가용 골든 정답셋 (설계서 6-6)

검색·판정 정확도의 **공식 기준**. 진미경(기획 오너)이 약관 원문을 확인하며 20~30개 작성,
이태경이 테스트 코드화·자동 채점기를 구현한다. 조윤의 RAG 튜닝 목표치도 이 채점으로 측정.

`cases/` 아래에 케이스별 JSON 을 둔다.

## 케이스 스키마

```jsonc
{
  "id": "golden-0001",
  "description": "한 줄 설명",
  "case": {                         // judge() 입력과 동일 형태
    "disease": "뇌경색",
    "disease_kcd": "I63",
    "surgery": false,
    "diag_days": 7,
    "current_days": 3,
    "policy_elapsed_days": 800,     // null → 면책·감액 "확인 불가"
    "claimed": ["현대 실손"]
  },
  "expected": [                     // 반드시 탐색돼야 하는 보장(정탐) — 누락 시 실패
    { "policy": "...", "rider": "...", "status": "eligible", "missed": true },
    { "policy": "...", "rider": "...", "status": "boundary_not_met", "gap_days": 1 }
  ],
  "must_not_match": [               // 잡히면 안 되는 보장(오탐 검증) — 정탐만큼 중요
    { "policy": "...", "rider": "..." }
  ]
}
```

- `status` 값: `eligible / claimed / boundary_not_met / waiting_period_not_met / not_applicable / potential`
- (선택) 실손 claim_rule 검증 케이스는 `expected[].calc` 에 formula 구조를 둔다.
- 검수 원칙: 정액 보장은 `claim_rule=null`, 실손만 작성 / 이중차감 금지.

채점 러너: [`../../scripts/eval_golden.py`](../../scripts/eval_golden.py) — 파이프라인 연결 후 CI 자동 채점.
