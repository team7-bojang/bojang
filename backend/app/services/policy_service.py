import threading
import uuid

from app.core.errors import NotFoundError
from app.db import get_client

_select_presets_lock = threading.Lock()


def get_presets() -> list[dict]:
    """선탑재 상품 목록을 반환합니다."""
    db = get_client()
    response = db.table("policies").select("*").eq("is_preset", True).execute()
    return response.data or []


def select_presets(user_id: str, preset_ids: list[str]) -> list[str]:
    """사용자가 선택한 preset 상품들을 복제하여 등록합니다."""
    db = get_client()
    registered_policy_ids = []

    # 404 처리를 위해 모든 preset_ids가 실재하는지 선검증
    for pid in preset_ids:
        res_p = db.table("policies").select("id").eq("id", pid).execute()
        if not res_p.data:
            raise NotFoundError(f"존재하지 않는 preset id가 포함되어 있습니다: {pid}")

    with _select_presets_lock:
        for pid in preset_ids:
            # 1. Preset 상품 조회
            res_policy = db.table("policies").select("*").eq("id", pid).execute()
            if not res_policy.data:
                continue
            preset_policy = res_policy.data[0]

            # 중복 방지: 이미 복제된 상품이 존재하는지 체크 (uq_policies_user_name_insurer 제약조건 방지)
            res_existing = (
                db.table("policies")
                .select("id")
                .eq("user_id", user_id)
                .eq("name", preset_policy["name"])
                .eq("insurer", preset_policy["insurer"])
                .eq("is_preset", False)
                .execute()
            )
            if res_existing.data:
                registered_policy_ids.append(res_existing.data[0]["id"])
                continue

            # 2. 상품 복제 (is_preset=False, user_id 할당)
            new_policy_id = str(uuid.uuid4())
            cloned_policy = {
                "id": new_policy_id,
                "name": preset_policy["name"],
                "insurer": preset_policy["insurer"],
                "type": preset_policy["type"],
                "is_preset": False,
                "pdf_path": preset_policy.get("pdf_path"),
            }
            # mock_db 및 real db에 user_id 저장을 위해 cases나 임의 필드 처리
            # 여기서는 policies 테이블에 user_id 칼럼이 SQL상 정의되어 있지 않지만,
            # meta 나 select를 위해 python mock_db에서 user_id로 구분이 가능하도록
            # meta에 보관하거나, mock_db는 동적 필드를 지원하므로
            # cloned_policy["user_id"] = user_id 형태로 처리
            cloned_policy["user_id"] = user_id
            db.table("policies").insert(cloned_policy).execute()

            # 3. 연결된 특약(riders) 복제
            res_riders = db.table("riders").select("*").eq("policy_id", pid).execute()

            riders_to_insert = []
            chunks_to_insert = []

            for r in res_riders.data or []:
                new_rider = r.copy()
                new_rider_id = str(uuid.uuid4())
                new_rider["id"] = new_rider_id
                new_rider["policy_id"] = new_policy_id
                new_rider["verified"] = True
                riders_to_insert.append(new_rider)

                # chunker를 사용해 rider_chunks 생성
                from app.rag.chunker import chunk_rider

                chunks = chunk_rider(new_rider)
                chunks_to_insert.extend(chunks)

            if riders_to_insert:
                db.table("riders").insert(riders_to_insert).execute()
            if chunks_to_insert:
                db.table("rider_chunks").insert(chunks_to_insert).execute()

            registered_policy_ids.append(new_policy_id)

    return registered_policy_ids


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
        "raw_text": (
            "피보험자가 질병으로 입원하여 치료를 받은 경우 입원 1일째부터 입원일당을 지급합니다."
        ),
    }
    db.table("riders").insert(cloned_rider).execute()

    from app.rag.chunker import chunk_rider

    for c in chunk_rider(cloned_rider):
        db.table("rider_chunks").insert(c).execute()

    return {"policy_id": new_policy_id, "status": "completed"}


def get_my_policies(user_id: str) -> list[dict]:
    """사용자가 등록한 보험 및 특약 목록을 조회합니다."""
    db = get_client()

    # 1. 사용자의 가입 보험 조회
    res_policies = db.table("policies").select("*").eq("user_id", user_id).execute()
    policies = res_policies.data or []

    results = []
    for p in policies:
        # 2. 각 보험에 대한 특약(riders) 조회
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


def get_source(policy_id: str, page: int) -> dict:
    """특정 보험 상품의 특정 페이지 약관 원문 텍스트를 조회합니다."""
    db = get_client()

    # riders 테이블에서 policy_id와 page가 매칭되는 레코드의 raw_text 검색
    res_riders = (
        db.table("riders").select("*").eq("policy_id", policy_id).eq("page", page).execute()
    )
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
