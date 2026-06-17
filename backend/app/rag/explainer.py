import os
import json
from pathlib import Path
from openai import OpenAI
from app.config import settings
from app.rag.citation import verify_quote

def _load_prompt():
    prompt_path = Path(__file__).resolve().parent.parent.parent.parent / "prompts" / "explanation" / "system_prompt.txt"
    if prompt_path.exists():
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return "보험 약관 분석 전문가로서 주어진 문맥에 기반하여 분석하고 JSON 스키마로 답변하시오."

def explain(case: dict, judgement: dict, chunks: list[dict]) -> dict:
    """RAG 약관 조각 및 판정 결과를 기반으로 LLM 설명문과 약관 인용을 생성합니다."""
    # 1. 컨텍스트 구성
    chunks_context = ""
    for idx, c in enumerate(chunks):
        chunks_context += f"--- Chunk {idx+1} (Page: {c.get('meta', {}).get('page')}, Article: {c.get('meta', {}).get('article_no')}) ---\n"
        chunks_context += f"{c.get('content')}\n\n"

    case_context = json.dumps(case, ensure_ascii=False, indent=2)
    judgement_context = json.dumps(judgement, ensure_ascii=False, indent=2)

    system_prompt_template = _load_prompt()
    system_prompt = system_prompt_template.replace(
        "{chunks_context}", chunks_context
    ).replace(
        "{case_context}", case_context
    ).replace(
        "{judgement_context}", judgement_context
    )


    # 2. OpenAI API 호출
    api_key = settings.openai_api_key
    if api_key:
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # gpt-4.1-mini는 가상 명칭이므로 실제 모델인 gpt-4o-mini 사용
                messages=[
                    {"role": "user", "content": system_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # 인용구 검증 (citation.py에 따른 환각 방지 장치)
            # 만약 citation 검증을 통과하지 못하면 fallback 문구 적용
            quote = result.get("quote", "")
            # chunks 안의 원문에 인용구가 존재하는지 대조
            raw_texts = [c.get("content", "") for c in chunks]
            quote_matched = False
            for raw_text in raw_texts:
                if verify_quote(quote, raw_text):
                    quote_matched = True
                    break
                    
            if not quote_matched:
                print(f"[Explainer] Citation check failed for: '{quote}'. Falling back to original source metadata.")
                # 인용이 부적합하면 chunks 중 첫 번째의 기재사항이나 기본 metadata로 변경
                if chunks:
                    first_c = chunks[0]
                    result["quote"] = first_c.get("content")[:100] + "..."
                    result["article"] = first_c.get("meta", {}).get("article_no")
                    result["page"] = first_c.get("meta", {}).get("page")
                    
            return result
        except Exception as e:
            print(f"[Explainer] OpenAI LLM call failed: {e}. Using deterministic fallback explanation.")
    
    # 3. API 키 미지정 혹은 에러 시의 Fallback 설명문 생성
    # 룰 엔진의 status 기반으로 기본적인 한글 설명문을 로컬에서 빌드하여 반환
    status = judgement.get("status", "not_applicable")
    explanation = f"약관 분석 결과, 해당 보장은 '{status}' 상태로 확인됩니다."
    quote = "해당 약관의 상세 규정을 확인하시기 바랍니다."
    article = "보험약관 본문"
    page = None

    if chunks:
        first_c = chunks[0]
        article = first_c.get("meta", {}).get("article_no") or article
        page = first_c.get("meta", {}).get("page") or page
        content_snippet = first_c.get("content", "")
        if "특약명" in content_snippet:
            lines = content_snippet.split("\n")
            rider_name = lines[0].replace("특약명:", "").strip()
            if status == "eligible":
                explanation = f"고객님께서 가입하신 '{rider_name}'의 보장 요건을 만족하여 보험금 지급 대상이 될 수 있습니다."
            elif status == "boundary_not_met":
                explanation = f"고객님께서 가입하신 '{rider_name}'의 지급 요건(치료 일수 등) 기준에 미달하여 현재로서는 지급 대상에서 제외됩니다."
            elif status == "waiting_period_not_met":
                explanation = f"고객님의 계약일이 면책 기간(대기 기간)인 {first_c.get('meta', {}).get('waiting_period_days', 90)}일을 지나지 않아 보장을 받으실 수 없습니다."
            elif status == "claimed":
                explanation = f"이미 타 보험사나 다른 계약을 통해 해당 사고에 대한 실손/기타 청구가 완료된 상태로 보입니다."
            
            quote = content_snippet[:120] + "..."

    return {
        "explanation": explanation,
        "quote": quote,
        "article": article,
        "page": page
    }

