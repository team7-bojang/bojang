"""F-01 약관 파싱·구조화 (진미경).

PDF → 텍스트/표 추출 → 섹션 분리(find_sections) → LLM 구조화 추출.
배치(전량 파싱)와 /policies/upload 가 공용으로 사용한다.
얇은 CLI 래퍼는 scripts/ (parse_policy.py·parse_rider.py).
"""
