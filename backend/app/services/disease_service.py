"""질병 검색 서비스 (SCR-03)."""

# KCD 질병 데이터 사전
_KCD_DATA = [
    {"kcd": "I63", "name": "뇌경색증"},
    {"kcd": "I60", "name": "지주막하출혈"},
    {"kcd": "I61", "name": "뇌내출혈"},
    {"kcd": "C16", "name": "위의 악성 신생물 (위암)"},
    {"kcd": "C34", "name": "폐암"},
    {"kcd": "M51", "name": "기타 추간판 장애 (허리디스크)"},
    {"kcd": "J30", "name": "혈관운동성 및 알레르기성 비염"},
    {"kcd": "E11", "name": "2형 당뇨병"},
    {"kcd": "I21", "name": "급성 심근경색증"}
]

def search_diseases(query: str) -> list[dict]:
    """검색어와 일치하는 질병명 및 KCD 코드를 반환합니다."""
    if not query:
        return _KCD_DATA
        
    results = []
    for item in _KCD_DATA:
        if query.lower() in item["name"].lower() or query.lower() in item["kcd"].lower():
            results.append(item)
            
    return results
