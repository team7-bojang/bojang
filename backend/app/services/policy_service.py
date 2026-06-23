import threading
import uuid

from app.core.errors import ForbiddenError, NotFoundError
from app.db import get_client

_select_presets_lock = threading.Lock()


def get_presets() -> list[dict]:
    """선탑재 상품 목록을 반환합니다."""
    db = get_client()
    response = db.table("policies").select("*").eq("is_preset", True).execute()
    return response.data or []


def select_presets(user_id: str, preset_ids: list[str]) -> list[str]:
    """사용자가 선택한 preset 상품들을 검증하고, 그 ID 목록을 그대로 반환합니다 (v2.1)."""
    db = get_client()

    # 404 처리를 위해 모든 preset_ids가 실재하는지 선검증 및 소유주/Preset 검증
    for pid in preset_ids:
        res_p = db.table("policies").select("id, is_preset, user_id").eq("id", pid).execute()
        if not res_p.data:
            raise NotFoundError(f"존재하지 않는 preset id가 포함되어 있습니다: {pid}")

        policy_data = res_p.data[0]
        if not policy_data.get("is_preset", False):
            if policy_data.get("user_id") != user_id:
                raise ForbiddenError("다른 사용자의 보험에 접근할 수 없습니다.")

    # 데이터 중복 폭발을 유발하는 상품/특약/청크 물리적 복제본을 만들지 않고 원본 preset_ids를 반환합니다.
    return preset_ids


def upload_pdf(user_id: str, file_name: str) -> dict:
    """약관 PDF 분석 후 상품 등록 예시 (스텁)."""
    db = get_client()
    new_policy_id = str(uuid.uuid4())

    # 임의로 PDF 분석 성공한 형태의 Mock 상품 및 특약 등록
    cloned_policy = {
        "id": new_policy_id,
        "name": f"업로드된 보험 ({file_name})",
        "insurer": "직접업로드",
        "type": "질병",
        "is_preset": False,
        "user_id": user_id,
    }
    db.table("policies").insert(cloned_policy).execute()

    # 기본 입원 특약 하나 매칭
    cloned_rider = {
        "id": str(uuid.uuid4()),
        "policy_id": new_policy_id,
        "name": "질병입원일당(1일이상)",
        "is_main": False,
        "trigger_type": "입원",
        "trigger_detail": "질병으로 1일이상 입원 치료 시",
        "unit_amount": 30000,
        "unit_type": "일시금",
        "unit_basis": "1일당 3만원 지급",
        "boundaries": [{"condition_days": 1, "effect": "1일이상"}],
        "exclusions": [],
        "limits": [],
        "waiting_period_days": 0,
        "reductions": [],
        "deduct_days": 0,
        "claim_rule": None,
        "verified": True,
        "page": 10,
        "article_no": "입원특약 제4조",
        "raw_text": ("피보험자가 질병으로 입원하여 치료를 받은 경우 입원 1일째부터 입원일당을 지급합니다."),
    }
    db.table("riders").insert(cloned_rider).execute()

    from app.rag.chunker import chunk_rider

    for c in chunk_rider(cloned_rider):
        db.table("rider_chunks").insert(c).execute()

    return {"policy_id": new_policy_id, "status": "completed"}


def get_my_policies(user_id: str) -> list[dict]:
    """사용자가 최근 생성한 Case의 보험 및 특약 목록을 조회합니다."""
    db = get_client()

    # 가장 최근 케이스 조회하여 사용된 policy_ids 추출
    res_case = (
        db.table("cases").select("policy_ids").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
    )

    policy_ids = []
    if res_case.data:
        policy_ids = res_case.data[0].get("policy_ids") or []

    if not policy_ids:
        return []

    # 해당 policy_ids를 가진 원본 preset policies 조회
    res_policies = db.table("policies").select("*").in_("id", policy_ids).execute()
    policies = res_policies.data or []

    results = []
    for p in policies:
        # 각 보험에 대한 특약(riders) 조회
        res_riders = db.table("riders").select("*").eq("policy_id", p["id"]).execute()
        results.append(
            {
                "policy": {
                    "id": p["id"],
                    "name": p["name"],
                    "insurer": p["insurer"],
                    "type": p["type"],
                },
                "riders": res_riders.data or [],
            }
        )

    return results


def get_source(policy_id: str, page: int, user_id: str) -> dict:
    """특정 보험 상품의 특정 페이지 약관 원문 텍스트를 조회합니다.

    선탑재 약관은 인증 유저 접근 허용.
    사용자 업로드 약관은 소유자만 접근 가능.
    """
    db = get_client()

    policy_res = db.table("policies").select("id, user_id, is_preset").eq("id", policy_id).single().execute()
    if not policy_res.data:
        raise NotFoundError("해당 약관을 찾을 수 없습니다.")
    if not policy_res.data.get("is_preset") and policy_res.data.get("user_id") != user_id:
        raise ForbiddenError("접근 권한이 없습니다.")

    # riders 테이블에서 policy_id와 page가 매칭되는 레코드의 raw_text 검색
    res_riders = db.table("riders").select("*").eq("policy_id", policy_id).eq("page", page).execute()
    if res_riders.data:
        rider = res_riders.data[0]
        return {"page": page, "text": rider.get("raw_text") or "원문 데이터가 존재하지 않습니다."}

    # 만약에 rider_chunks 테이블에서 찾아본다면
    res_chunks = (
        db.table("rider_chunks")
        .select("*, riders(*)")
        .eq("meta->policy_id", policy_id)
        .eq("meta->page", page)
        .execute()
    )
    if res_chunks.data:
        chunk = res_chunks.data[0]
        return {"page": page, "text": chunk.get("content")}

    raise NotFoundError("해당 페이지의 약관 원문을 찾을 수 없습니다.")
