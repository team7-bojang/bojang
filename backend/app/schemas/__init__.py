"""Pydantic 스키마 = Swagger 자동 문서의 단일 소스 (설계서 §4).

요청/응답 검증 겸용. 프론트엔드 타입은 /docs(OpenAPI) → openapi-typescript 로 생성해
계약을 일치시킨다. 충돌 우선순위: mocks/ > API 명세서 > 본 스키마.
"""
