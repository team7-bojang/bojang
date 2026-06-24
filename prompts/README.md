# prompts

프롬프트·공통 JSON 스키마 **일원화** 디렉터리 (최종 승인: 조윤).

| 폴더 | 용도 | 사용처 |
| --- | --- | --- |
| `parsing/` | 약관 구조화 추출 템플릿·예시 (진미경 제작) | `app/parsing/structurer.py` |
| `parsing/medical_statement_vision_prompt.txt` | 진료비 세부산정내역서 사진(Vision LLM) 구조화 추출 | `app/parsing/medical_statement.py::parse_medical_statement_image` |
| `explanation/` | 탐색 설명 생성 프롬프트 (원문 컨텍스트 한정) | `app/rag/explainer.py` |

원칙: 코드에 프롬프트 문자열을 하드코딩하지 않고 이 디렉터리의 파일을 로드한다.
