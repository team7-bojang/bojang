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
os.environ["DEBUG"] = "True"

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
    user_id = "golden-test-user-uuid"
    
    # 이전에 테스트 데이터가 있다면 초기화
    db.table("policies").data_list = [p for p in db.table("policies").data_list if p.get("user_id") != user_id]
    
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
        init_res = case_service.create_case(user_id, f"골든셋 평가: {input_data.get('disease', '상황')}")
        temp_case_id = init_res["case_id"]
        
        # 골든셋 케이스 조건으로 덮어쓰기
        case_service.patch_extracted_info(user_id, temp_case_id, {
            "disease_kcd": input_data.get("disease_kcd"),
            "disease_name": input_data.get("disease"),
            "surgery": input_data.get("surgery", False),
            "diag_days": input_data.get("diag_days", 0),
            "current_days": input_data.get("current_days", 0),
            "policy_elapsed_days": input_data.get("policy_elapsed_days"),
            "claimed_policy_ids": input_data.get("claimed", [])
        })
        
        # 3. 보장 탐색 실행
        analysis_res = analysis_service.search_analysis(user_id, temp_case_id)
        results = analysis_res.get("results", [])
        
        # 4. 정탐(Expected) 검증
        case_passed = True
        print("  - 정탐(Expected) 검증:")
        for exp in expected:
            # 예상되는 상품과 특약이 매칭되었는지 확인
            match = next((r for r in results if r["policy"] == exp["policy"] and r["rider"] == exp["rider"]), None)
            if not match:
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
            if match:
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
