from __future__ import annotations

import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR if (SCRIPT_DIR / "rider_catalog.json").exists() else SCRIPT_DIR / "golden_set_v2"
ALLOWED_STATUS = {
    "eligible", "claimed", "boundary_not_met", "waiting_period_not_met",
    "verification_required", "not_applicable", "potential",
}


def main() -> None:
    catalog = json.loads((ROOT / "rider_catalog.json").read_text(encoding="utf-8"))
    files = sorted((ROOT / "cases").glob("*.json"))
    assert len(files) == 12, f"expected 12 cases, got {len(files)}"

    ids = set()
    errors = []
    expected_count = 0
    for path in files:
        case = json.loads(path.read_text(encoding="utf-8"))
        if case["id"] in ids:
            errors.append(f"{path.name}: duplicate id {case['id']}")
        ids.add(case["id"])
        if case["service_type"] not in {"CASE1", "CASE2"}:
            errors.append(f"{path.name}: invalid service_type")

        for result in case["expected"]:
            expected_count += 1
            if result["status"] not in ALLOWED_STATUS:
                errors.append(f"{path.name}: invalid status {result['status']}")
            if result["estimated_amount"] is not None and result["estimated_amount"] < 0:
                errors.append(f"{path.name}: negative amount")
            key = result["rider_catalog_key"]
            if key not in catalog:
                errors.append(f"{path.name}: missing rider catalog key {key}")
            if result["status"] != "eligible" and result["estimated_amount"] not in {0, None}:
                errors.append(f"{path.name}: non-eligible result has positive amount")
            reduction = result.get("reduction")
            if reduction and result["status"] != "eligible":
                errors.append(f"{path.name}: reduction must accompany eligible")
            amount_basis = result.get("amount_basis")
            if not amount_basis:
                errors.append(f"{path.name}: missing amount_basis")
            elif result["status"] == "eligible" and not amount_basis.get("demo_input"):
                errors.append(f"{path.name}: eligible result missing demo amount input")
            steps = result.get("calculation_steps", [])
            if not steps or steps[-1].get("title") != "최종 예상보험금":
                errors.append(f"{path.name}: missing calculation steps")

        if case.get("comparison_basis") == "POLICY_ELAPSED":
            for result in case["expected"]:
                if result["status"] == "waiting_period_not_met" and "gap_days" in result:
                    errors.append(f"{path.name}: range-based waiting result must not expose gap_days")

        summaries = case.get("policy_amount_summary", [])
        summarized_policies = {row["policy"] for row in summaries}
        missing_policies = set(case["selected_policies"]) - summarized_policies
        if missing_policies:
            errors.append(f"{path.name}: policies missing amount summary {sorted(missing_policies)}")

        expected_totals = {}
        for result in case["expected"]:
            if result["status"] != "eligible":
                continue
            key = result["policy"], result.get("scenario_days")
            expected_totals[key] = expected_totals.get(key, 0) + result["estimated_amount"]
        for summary in summaries:
            key = summary["policy"], summary.get("scenario_days")
            expected = expected_totals.get(key, 0)
            if summary["estimated_amount"] != expected:
                errors.append(
                    f"{path.name}: policy summary mismatch {key}: "
                    f"expected={expected}, actual={summary['estimated_amount']}"
                )
            breakdown_total = sum(
                row["estimated_amount"] for row in summary.get("calculation_breakdown", [])
            )
            if breakdown_total != summary["estimated_amount"]:
                errors.append(
                    f"{path.name}: policy breakdown mismatch {key}: "
                    f"expected={summary['estimated_amount']}, actual={breakdown_total}"
                )

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        raise SystemExit(1)

    print(f"OK: {len(files)} cases, {expected_count} expected rows, {len(catalog)} rider snapshots")


if __name__ == "__main__":
    main()
