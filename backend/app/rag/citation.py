"""인용 검증 (NFR-01) — LLM 인용문 ↔ riders.raw_text 문자열 대조.

불일치 시 해당 결과 폐기·재생성(최대 2회), 재실패 시 원문 링크만 제공.
환각 방지 3중 장치 중 코드 단계 (LLM 아님).
"""

# TODO: verify_quote(quote, raw_text) -> bool
