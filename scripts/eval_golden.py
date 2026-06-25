"""골든 정답셋으로 RAG·Judge 품질을 평가하는 러너.

사용:
    python scripts/eval_golden.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서도 한글 출력이 깨지지 않도록 UTF-8 고정
_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8")

# 백엔드 모듈 임포트를 위해 sys.path 추가
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.append(str(BACKEND_DIR))

# 환경 변수 강제 주입 및 기본 설정
import os
os.chdir(BACKEND_DIR)
os.environ["DEBUG"] = "True"
os.environ["MOCK_LLM"] = "True"

from app.db import get_client
from app.services import policy_service, case_service, analysis_service

GOLDEN_DIR = Path(__file__).resolve().parent.parent / "tests" / "golden" / "cases"


def load_cases() -> list[dict]:
    cases = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GOLDEN_DIR.glob("*.json"))]
    print(f"[golden] {len(cases)} 케이스 로드: {GOLDEN_DIR}")
    return cases


def main() -> None:
    # 1. DB 초기화 및 테스트 유저 프리셋 등록
    db = get_client()
    user_id = "00000000-0000-0000-0000-000000000000"
    
    # 이전에 테스트 데이터가 있다면 초기화
    if hasattr(db.table("policies"), "data_list"):
        db.table("policies").data_list = [
            p for p in db.table("policies").data_list if p.get("user_id") != user_id
        ]
    else:
        try:
            res_p = db.table("policies").select("id").eq("user_id", user_id).execute()
            p_ids = [p["id"] for p in res_p.data or []]
            if p_ids:
                for pid in p_ids:
                    db.table("rider_chunks").delete().eq("meta->>policy_id", pid).execute()
                db.table("riders").delete().in_("policy_id", p_ids).execute()
                db.table("policies").delete().eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[golden] Real DB clean up failed: {e}")
    
    # Preset 상품 4개 등록
    presets = policy_service.get_presets()
    preset_ids = [p["id"] for p in presets]
    policy_service.select_presets(user_id, preset_ids)
    
    cases = load_cases()
    passed_all = True
    
    for c in cases:
        case_id = c["id"]
        description = c["description"]
        input_data = c["case"]
        expected = c.get("expected", [])
        must_not_match = c.get("must_not_match", [])
        
        print(f"\n[Run] {case_id}: {description}")
        
        # 2. Case 임시 생성 및 골든셋 인풋 주입
        # POST /cases 처럼 동작
        init_res = case_service.create_case(
            user_id,
            "CASE1",
            preset_ids,
            f"골든셋 평가: {input_data.get('disease', '상황')}"
        )
        temp_case_id = init_res["case_id"]
        
        # 골든셋 케이스 조건으로 덮어쓰기
        case_service.patch_extracted_info(user_id, temp_case_id, {
            "disease_kcd": input_data.get("disease_kcd"),
            "disease_name": input_data.get("disease"),
            "surgery": input_data.get("surgery", False),
            "diag_days": input_data.get("diag_days") or input_data.get("admission_days_diagnosed") or 0,
            "current_days": input_data.get("current_days") or input_data.get("admission_days_current") or 0,
            "policy_elapsed_days": input_data.get("policy_elapsed_days"),
            "claimed_policy_ids": input_data.get("claimed", []),
            "treatment_items": input_data.get("treatment_items") or []
        })
        
        # 3. 보장 탐색 실행
        analysis_res = analysis_service.search_analysis(user_id, temp_case_id)
        results = analysis_res.get("results", [])

        # CASE2처럼 scenario_days별로 다른 정답이 기대되는 케이스는
        # 단일 search_analysis 결과로 비교할 수 없으므로 compare_scenarios로 일수별 결과를 따로 확보한다.
        scenario_lookup = {}
        scenario_days_values = {e["scenario_days"] for e in expected if e.get("scenario_days") is not None}
        if scenario_days_values:
            current_days = input_data.get("admission_days_current")
            target_days = input_data.get("admission_days_diagnosed")
            if current_days is not None and target_days is not None and current_days != target_days:
                compare_res = analysis_service.compare_scenarios(
                    user_id, temp_case_id, current_days=current_days, target_days=target_days
                )
                for comp in compare_res.get("comparison", []):
                    for sc in comp.get("scenarios", []):
                        key = (comp["policy_name"], comp["rider_name"], sc.get("days"))
                        scenario_lookup[key] = sc

        # 4. 정탐(Expected) 검증
        case_passed = True
        print("  - 정탐(Expected) 검증:")
        for exp in expected:
            # scenario_days가 있는 기대값은 compare_scenarios 결과에서, 없으면 search_analysis 결과에서 찾는다
            scenario_days = exp.get("scenario_days")
            if scenario_days is not None and scenario_lookup:
                match = scenario_lookup.get((exp["policy"], exp["rider"], scenario_days))
            else:
                match = next((r for r in results if r["policy"] == exp["policy"] and r["rider"] == exp["rider"]), None)

            if not match:
                # analysis_service는 not_applicable이고 추가 지급액이 없는 결과는
                # 화면에 보여줄 필요가 없어 결과 목록에서 의도적으로 제외한다(analysis_service.py 참고).
                # 골든셋도 이 경우 "검색 안 됨"을 not_applicable 확정으로 보고 통과 처리한다.
                if exp.get("status") == "not_applicable" and not exp.get("estimated_amount"):
                    print(f"    ✓ 통과(설계상 비노출): [{exp['policy']}] {exp['rider']} (not_applicable)")
                    continue
                print(f"    ❌ 미검색: [{exp['policy']}] {exp['rider']}")
                case_passed = False
                passed_all = False
            else:
                # 상태 및 gap_days 검증
                status_match = match["status"] == exp["status"]
                gap_match = True
                if "gap_days" in exp:
                    gap_match = match.get("gap_days") == exp["gap_days"]

                if status_match and gap_match:
                    print(f"    ✓ 통과: [{exp['policy']}] {exp['rider']} ({match['status']})")
                else:
                    print(f"    ❌ 불일치: [{exp['policy']}] {exp['rider']} (기대값: {exp['status']} / 실제: {match['status']}, gap_days 기대값: {exp.get('gap_days')} / 실제: {match.get('gap_days')})")
                    case_passed = False
                    passed_all = False

        # 5. 오탐(Must Not Match) 검증
        print("  - 오탐(Must Not Match) 검증:")
        for mnm in must_not_match:
            match = next((r for r in results if r["policy"] == mnm["policy"] and r["rider"] == mnm["rider"]), None)
            if match and match.get("status") in ["eligible", "potential", "claimed"]:
                print(f"    ❌ 오탐지: [{mnm['policy']}] {mnm['rider']} ({match['status']})")
                case_passed = False
                passed_all = False
            else:
                print(f"    ✓ 미감지(통과): [{mnm['policy']}] {mnm['rider']}")
                
        if case_passed:
            print(f"  🎉 케이스 {case_id} 통과!")
        else:
            print(f"  🚨 케이스 {case_id} 실패!")
            
    if passed_all:
        print("\n🏆 모든 골든셋 검증 케이스 통과! (RAG + Judge 완벽 동작)")
        sys.exit(0)
    else:
        print("\n❌ 일부 검증 케이스가 실패했습니다. RAG 검색 또는 판정 로직을 보완해 주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
