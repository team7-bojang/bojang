"""골든 정답셋으로 RAG·Judge 품질을 평가하는 러너 (스텁).

사용:
    python scripts/eval_golden.py

현재는 케이스 로딩/스키마 검증까지만 수행한다.
파이프라인(app.pipeline.retrieve / judge)이 구현되면 아래 TODO 부분을 채운다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서도 한글 출력이 깨지지 않도록 UTF-8 고정
_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8")

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden" / "cases"


def load_cases() -> list[dict]:
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GOLDEN_DIR.glob("*.json"))]
    print(f"[golden] {len(cases)} 케이스 로드: {GOLDEN_DIR}")
    return cases


def main() -> None:
    cases = load_cases()
    for case in cases:
        # TODO: 파이프라인 실행 후 expected 와 비교해 지표 집계
        #   predicted = run_pipeline(case["input"])
        #   score = compare(predicted, case["expected"])
        print(f"  - {case['id']}: {case['description']}")
    print("[golden] TODO: 파이프라인 연결 후 정확도/근거 일치율 집계")


if __name__ == "__main__":
    main()
