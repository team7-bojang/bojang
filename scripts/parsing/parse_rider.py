"""약관 파싱 파이프라인 (F-01) — 보장 단위 구조화.

사용법 (스프린트 워크플로):
  1. 목차에서 파싱할 보장의 페이지 범위를 찾는다 (목차 캡처 활용)
  2. python scripts/parsing/parse_rider.py <약관.pdf> --pages 96-98 --out data/parsed/db_뇌혈관.json
  3. 출력 JSON ↔ 약관 원문 대조 검증 후 진미경에게 제출 (verified=false 상태)

옵션:
  --pages 96-98     파싱할 PDF 페이지 범위 (필수) — 특약 1~2개가 들어가는 범위로 좁게
  --out FILE        출력 JSON 경로 (기본: data/parsed/<pdf명>_<pages>.json)
  --dry-run         LLM 호출 없이 추출 텍스트·표·프롬프트만 출력 (페이지 범위 확인용)
  --model           기본 claude-sonnet-4-6

환경변수: ANTHROPIC_API_KEY
의존성: pip install -r requirements.txt
"""

import argparse
import json
from pathlib import Path

import pdfplumber
from rider_schema import ParseResult

# scripts/parsing/ → 저장소 루트 (prompts·data·.env 의 단일 기준점)
ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")  # 저장소 루트 .env (실행 위치 무관)
except ImportError:
    pass  # python-dotenv 미설치 시 OS 환경변수만 사용

# 프롬프트는 prompts/parsing/ 에 일원화 (코드 하드코딩 금지 규약)
PROMPT_PATH = ROOT / "prompts" / "parsing" / "rider_extraction_prompt.txt"


def clean(text: str) -> str:
    """추출 텍스트 정리 — 이 약관류 PDF는 공백이 NUL(\\x00)로 추출되는 경우가 있음."""
    return text.replace("\x00", " ").replace("\xa0", " ")


def extract_pages(
    pdf_path: str, page_from: int, page_to: int, snapshot_dir: str | None = None
) -> str:
    """페이지 범위의 텍스트 + 표를 [PAGE n]·[TABLE] 마커와 함께 추출.

    주의: 2단 레이아웃 약관에서 표 추출(extract_tables)이 불완전할 수 있다.
    감액·한도 등 표의 값은 일반 텍스트에도 포함되므로 LLM이 재구성하지만,
    표가 걸린 페이지는 --snapshot으로 이미지를 떠서 반드시 육안 대조한다 (판단 가이드 2).
    """
    blocks = []
    with pdfplumber.open(pdf_path) as pdf:
        if page_from > len(pdf.pages):
            raise ValueError(f"오류: PDF는 {len(pdf.pages)}페이지까지입니다 (요청: {page_from})")

        if page_to > len(pdf.pages):
            print(f"  ⚠️ 페이지 범위 보정: p.{page_from}-{page_to} → p.{page_from}-{len(pdf.pages)}")
            page_to = len(pdf.pages)

        for i in range(page_from - 1, page_to):
            page = pdf.pages[i]
            blocks.append(f"[PAGE {i + 1}]")
            blocks.append(clean(page.extract_text() or "(텍스트 없음)"))
            for t_idx, table in enumerate(page.extract_tables()):
                rows = [" | ".join(clean(c or "").replace("\n", " ") for c in row) for row in table]
                rows = [r for r in rows if r.strip(" |")]  # 빈 행 제거
                if rows:
                    blocks.append(
                        f"[TABLE {i + 1}-{t_idx + 1}] "
                        "(보조 — 불완전할 수 있음, 본문 텍스트와 교차 확인)\n" + "\n".join(rows)
                    )
            if snapshot_dir:
                Path(snapshot_dir).mkdir(parents=True, exist_ok=True)
                img_path = Path(snapshot_dir) / f"{Path(pdf_path).stem}_p{i + 1}.png"
                try:
                    page.to_image(resolution=120).save(img_path)
                    print(f"  스냅샷 저장: {img_path} (검수용)")
                except Exception as e:  # Pillow 미설치 등
                    print(f"  스냅샷 생략 ({e})")
    return "\n\n".join(blocks)


def call_llm(system_prompt: str, document: str, model: str) -> str:
    import anthropic  # 지연 임포트 — dry-run은 SDK 없이도 동작

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 사용
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": (
                    "다음 약관 추출 텍스트에서 보장(rider)을 구조화하세요. "
                    "JSON 객체만 출력하세요.\n\n" + document
                ),
            }
        ],
    )
    # content는 블록 유니온(text/thinking/tool_use…) → text 블록만 좁혀서 .text 접근
    block = msg.content[0]
    if block.type != "text":
        raise RuntimeError(f"예상치 못한 응답 블록 타입: {block.type}")
    return block.text


def parse_json_strict(text: str) -> dict:
    """LLM 출력에서 JSON 객체 파싱 (백틱 펜스 방어).
    보장이 없는 페이지(목차·요약)는 LLM이 빈 응답·설명문을 줄 수 있으므로
    JSON을 못 찾으면 빈 결과로 처리한다 (실패가 아님)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        cleaned = cleaned.removeprefix("json").strip()
    # JSON 객체 시작이 없으면(설명문·빈응답) 빈 결과
    brace = cleaned.find("{")
    if brace == -1:
        return {"riders": []}
    cleaned = cleaned[brace : cleaned.rfind("}") + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"riders": []}


def main() -> None:
    ap = argparse.ArgumentParser(description="약관 보장 구조화 파이프라인 (F-01)")
    ap.add_argument("pdf")
    ap.add_argument("--pages", required=True, help="예: 96-98 (단일 페이지는 97-97)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--snapshot", default=None, help="검수용 페이지 PNG 저장 디렉토리")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args()

    page_from, page_to = (int(x) for x in args.pages.split("-"))
    document = extract_pages(args.pdf, page_from, page_to, snapshot_dir=args.snapshot)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    if args.dry_run:
        print("=" * 30, "추출 텍스트·표 (LLM 입력)", "=" * 30)
        print(document)
        print("=" * 30, f"(시스템 프롬프트 {len(system_prompt)}자 별도)", "=" * 30)
        return

    raw = call_llm(system_prompt, document, args.model)
    data = parse_json_strict(raw)

    # pydantic 검증 — 스키마 v1.1 위반 시 여기서 실패 (형식 분기 차단)
    result = ParseResult(**data)
    for rider in result.riders:
        rider.verified = False  # 파싱 출력은 무조건 검수 대기

    out_path = Path(
        args.out or ROOT / "data" / "parsed" / f"{Path(args.pdf).stem}_{args.pages}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"✓ {len(result.riders)}개 보장 구조화 → {out_path}")
    print("  다음 단계: JSON ↔ 약관 원문 대조 검증 후 제출 (검수: 진미경)")


if __name__ == "__main__":
    main()
