"""질병 검색 서비스 (SCR-03)."""

from app.db import get_client

# KCD 질병 데이터 사전 (Fallback 용)
_KCD_DATA = [
    {"kcd": "I63", "name": "뇌경색증"},
    {"kcd": "I60", "name": "지주막하출혈"},
    {"kcd": "I61", "name": "뇌내출혈"},
    {"kcd": "C16", "name": "위의 악성 신생물 (위암)"},
    {"kcd": "C34", "name": "폐암"},
    {"kcd": "M51", "name": "기타 추간판 장애 (허리디스크)"},
    {"kcd": "J30", "name": "혈관운동성 및 알레르기성 비염"},
    {"kcd": "E11", "name": "2형 당뇨병"},
    {"kcd": "I21", "name": "급성 심근경색증"},
]


def search_diseases(query: str, limit: int = 5, offset: int = 0) -> dict:
    """검색어와 일치하는 질병명 및 KCD 코드를 페이징하여 반환합니다."""
    client = get_client()
    try:
        if not query:
            res = (
                client.table("diseases").select("kcd, name", count="exact").range(offset, offset + limit - 1).execute()
            )
            total = res.count or 0
            results = res.data or []
        else:
            res = (
                client.table("diseases")
                .select("kcd, name", count="exact")
                .or_(f"name.ilike.%{query}%,kcd.ilike.%{query}%,search_text.ilike.%{query}%")
                .range(offset, offset + limit - 1)
                .execute()
            )
            total = res.count or 0
            results = res.data or []

        has_more = (offset + limit) < total
        return {"results": results, "total": total, "offset": offset, "has_more": has_more}
    except Exception as e:
        print(f"[DiseaseService] Failed to fetch diseases from Supabase: {e}")
        # Local fallback
        if not query:
            filtered = _KCD_DATA
        else:
            filtered = [
                item
                for item in _KCD_DATA
                if query.lower() in item["name"].lower() or query.lower() in item["kcd"].lower()
            ]
        total = len(filtered)
        results = filtered[offset : offset + limit]
        has_more = (offset + limit) < total
        return {"results": results, "total": total, "offset": offset, "has_more": has_more}
