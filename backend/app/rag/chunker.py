def chunk_rider(rider: dict) -> list[dict]:
    chunks = []
    rider_id = rider.get("id")
    name = rider.get("name", "")
    trigger_detail = rider.get("trigger_detail") or ""
    unit_basis = rider.get("unit_basis") or ""
    exclusions = rider.get("exclusions") or []
    limits = rider.get("limits") or []
    reductions = rider.get("reductions") or []

    # 1. 보장 대상 및 지급 기준 청크
    content_cov = f"특약명: {name}\n보장 사유 및 대상: {trigger_detail}\n지급 기준: {unit_basis}"
    chunks.append(
        {
            "rider_id": rider_id,
            "content": content_cov.strip(),
            "meta": {
                "policy_id": rider.get("policy_id"),
                "page": rider.get("page"),
                "article_no": rider.get("article_no"),
                "trigger_type": rider.get("trigger_type"),
                "type": "coverage",
            },
        }
    )

    # 2. 보장 제외(면책) 사항 청크
    if exclusions:
        exclusion_text = "\n".join([f"- {item}" for item in exclusions])
        content_excl = f"특약명: {name}\n보장하지 않는 사항 (면책/제외): {exclusion_text}"
        chunks.append(
            {
                "rider_id": rider_id,
                "content": content_excl.strip(),
                "meta": {
                    "policy_id": rider.get("policy_id"),
                    "page": rider.get("page"),
                    "article_no": rider.get("article_no"),
                    "trigger_type": rider.get("trigger_type"),
                    "type": "exclusions",
                },
            }
        )

    # 3. 한도 및 감액 조건 청크
    if limits or reductions:
        limit_text = "\n".join([f"- {item}" for item in limits]) if limits else "없음"
        reduction_text = "\n".join([f"- {item}" for item in reductions]) if reductions else "없음"
        content_lim = f"특약명: {name}\n지급 한도: {limit_text}\n감액 규정: {reduction_text}"
        chunks.append(
            {
                "rider_id": rider_id,
                "content": content_lim.strip(),
                "meta": {
                    "policy_id": rider.get("policy_id"),
                    "page": rider.get("page"),
                    "article_no": rider.get("article_no"),
                    "trigger_type": rider.get("trigger_type"),
                    "type": "limits",
                },
            }
        )

    return chunks
