"""골든 정답셋 v2 평가기 템플릿.

실제 백엔드 호출부 `run_backend(case)`만 프로젝트 구현에 맞게 연결하면 된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
GOLDEN_ROOT = SCRIPT_DIR if (SCRIPT_DIR / "cases").exists() else SCRIPT_DIR / "golden_set_v2"
GOLDEN_DIR = GOLDEN_ROOT / "cases"


def run_backend(case: dict[str, Any]) -> list[dict[str, Any]]:
    raise NotImplementedError("analysis/search 또는 analysis/compare 호출부를 연결하세요.")


def result_key(row: dict[str, Any]) -> tuple:
    return row.get("policy"), row.get("rider"), row.get("scenario_days")


def compare_case(case: dict[str, Any], actual: list[dict[str, Any]]) -> list[str]:
    errors = []
    actual_by_key = {result_key(row): row for row in actual}

    for expected in case["expected"]:
        key = result_key(expected)
        found = actual_by_key.get(key)
        if found is None:
            errors.append(f"미검색: {key}")
            continue
        for field in ("status", "gap_days", "payable_days", "estimated_amount"):
            if field in expected and found.get(field) != expected.get(field):
                errors.append(
                    f"{key} {field} 불일치: expected={expected.get(field)!r}, actual={found.get(field)!r}"
                )
        if "reduction" in expected:
            expected_reduction = expected["reduction"]
            actual_reduction = found.get("reduction") or {}
            for field in ("applied", "rate", "until_elapsed_days"):
                if actual_reduction.get(field) != expected_reduction.get(field):
                    errors.append(
                        f"{key} reduction.{field} 불일치: "
                        f"expected={expected_reduction.get(field)!r}, actual={actual_reduction.get(field)!r}"
                    )

    actual_pairs = {(row.get("policy"), row.get("rider")) for row in actual}
    for forbidden in case["must_not_match"]:
        pair = forbidden["policy"], forbidden["rider"]
        if pair in actual_pairs:
            errors.append(f"오탐: {pair}")

    if case.get("expected_summary", {}).get("empty_result") and actual:
        errors.append(f"빈 결과 기대지만 {len(actual)}건 반환")

    expected_totals = {
        (row["policy"], row.get("scenario_days")): row["estimated_amount"]
        for row in case.get("policy_amount_summary", [])
    }
    actual_totals = {}
    for row in actual:
        if row.get("status") != "eligible":
            continue
        key = row.get("policy"), row.get("scenario_days")
        actual_totals[key] = actual_totals.get(key, 0) + (row.get("estimated_amount") or 0)
    for key, amount in expected_totals.items():
        if actual_totals.get(key, 0) != amount:
            errors.append(
                f"{key} 보험별 예상금액 불일치: expected={amount}, "
                f"actual={actual_totals.get(key, 0)}"
            )
    return errors


def main() -> None:
    failed = False
    for path in sorted(GOLDEN_DIR.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        try:
            actual = run_backend(case)
        except NotImplementedError as error:
            print(error)
            return
        errors = compare_case(case, actual)
        if errors:
            failed = True
            print(f"FAIL {case['id']}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"PASS {case['id']}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
