# tests

테스트는 성격에 따라 두 곳으로 나뉩니다.

| 위치 | 종류 | 실행 |
| --- | --- | --- |
| `backend/tests/` | 백엔드 단위·통합 테스트 (pytest) | `cd backend && pytest` |
| `tests/golden/` | RAG·Judge **품질 평가용 골든 정답셋(데이터)** | `python scripts/eval_golden.py` |

## golden 이란?

코드의 통과/실패를 보는 일반 테스트가 아니라, **"입력(가입정보·질병·입원) → 기대 보장/약관 근거"** 정답 쌍을 모아둔
평가 데이터셋입니다. 파이프라인(retrieve + judge)을 이 정답셋에 돌려
정확도·재현율·근거 일치율 등 품질 지표를 측정합니다.

스키마와 예시는 [`golden/README.md`](golden/README.md) 참고.
