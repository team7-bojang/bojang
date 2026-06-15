"""비즈니스 로직 계층 (라우트 ↔ rag/judge/parsing/db 오케스트레이션).

analysis_service 가 핵심: retrieve(rag) → judge(룰엔진) → explain(rag) → 인용검증(rag.citation)
순서로 조립하며, 판정은 반드시 judge() 순수 함수만 호출한다.
"""
