"""약관 1건 전체 자동 파싱 (find_sections + parse_rider 통합).

사람이 페이지를 고르지 않는다. 키워드로 후보 구간을 전부 찾아
각 구간을 자동으로 파싱하고, 결과를 보장(rider) 단위로 하나의 JSON에 합친다.

사용법:
  python parse_policy.py 약관.pdf
  python parse_policy.py 약관.pdf --keywords 입원일당 골절 암진단 진단자금
  python scripts/parsing/parse_policy.py 약관.pdf --out data/parsed/db_전체.json

동작:
  1. find_sections 로직으로 '보험금의 지급사유' 동반 후보 구간 전부 탐색
  2. 각 구간을 parse_rider 로직으로 파싱 (구간당 LLM 1회 호출)
  3. rider들을 합쳐 하나의 JSON으로 저장 (verified=false)
  4. 검수용 스냅샷 페이지 PNG 저장

주의:
  - 구간 수만큼 LLM을 호출하므로, 큰 약관(교보·KB)은 호출이 여러 번 → 시간·토큰 소요
  - 중복 보장(같은 rider가 여러 구간에 등장) 가능 → 검수 시 정리
  - 결과는 전량 후보이므로 핵심/주변 보장이 섞임 — verified=false로 적재 후 선별 검수
"""

import argparse
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from find_sections import DEFAULT_KEYWORDS, group_ranges, scan, split_by_rider_title
from parse_rider import PROMPT_PATH, call_llm, extract_pages, parse_json_strict
from rider_schema import ParseResult

# scripts/parsing/ → 저장소 루트 (data·.env 의 단일 기준점)
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def main() -> None:
    ap = argparse.ArgumentParser(description="약관 1건 전체 자동 파싱 (탐색→파싱→병합)")
    ap.add_argument("pdf")
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    ap.add_argument(
        "--all-hits",
        action="store_true",
        help="'보험금의 지급사유' 동반 조건 없이 키워드 등장 구간 전부",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="키워드 무시, '보험금의 지급사유' 있는 모든 페이지 파싱 (빠짐없이 — 통원·도수·항암 등 포함, 전량 파싱 권장)",
    )
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--no-snapshot", action="store_true", help="검수용 스냅샷 생략")
    ap.add_argument(
        "--max-ranges",
        type=int,
        default=0,
        help="안전장치: 파싱할 최대 구간 수 (0=무제한). 큰 약관 테스트 시 제한용",
    )
    ap.add_argument(
        "--by-page",
        action="store_true",
        help="특약 제목 분할을 끄고 지급사유 페이지 묶음 방식 사용 (제목이 불규칙한 약관용)",
    )
    ap.add_argument(
        "--max-section-pages",
        type=int,
        default=4,
        help="특약 제목 분할 시 한 구간의 최대 페이지 수 (기본 4)",
    )
    args = ap.parse_args()

    pdf_name = Path(args.pdf).name
    stem = Path(args.pdf).stem
    snapshot_dir = None if args.no_snapshot else str(ROOT / "data" / "parsed" / "snapshots" / stem)

    # 1. 후보 구간 탐색 — 특약 제목 단위 분할이 기본(누락 방지). 제목 없으면 지급사유 방식 폴백.
    ranges = []
    if not args.by_page:
        print("[1/3] 후보 구간 탐색 중... (특약 제목 단위 분할)")
        ranges = split_by_rider_title(args.pdf, max_pages_per_section=args.max_section_pages)
        if ranges:
            print(f"      특약 제목 {len(ranges)}개 구간으로 분할")
        else:
            print("      특약 제목 패턴 없음 → 지급사유 페이지 묶음 방식으로 폴백")
    if not ranges:
        mode = "전량(지급사유 전체)" if args.full else "키워드: " + ", ".join(args.keywords)
        print(f"[1/3] 후보 구간 탐색 중... ({mode})")
        hits = scan(args.pdf, args.keywords, require_trigger=not args.all_hits, full=args.full)
        ranges = group_ranges(hits)
    if not ranges:
        print("후보 구간 없음 — --all-hits 또는 키워드를 바꿔 재시도하세요.")
        return
    if args.max_ranges:
        ranges = ranges[: args.max_ranges]
    print(f"      후보 {len(ranges)}개 구간:")
    for p_from, p_to, kws in ranges:
        print(f"        p.{p_from}-{p_to}  ({', '.join(sorted(str(k) for k in kws))})")

    # 2. 각 구간 파싱
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    all_riders = []
    seen = set()  # (name, page) 중복 제거용
    failed = []
    warnings = []  # (rider_name, [경고들])
    quote_mismatch = []  # raw_text가 원문에 없는 경우

    def _norm(s: str) -> str:
        # 의미를 바꾸지 않는 표기 차이만 흡수해 substring 대조 (LLM의 사소한 변형 허용).
        # 곡선 따옴표↔직선, 가운뎃점류 제거, 공백 제거. 단어·숫자가 바뀐 진짜 변형은 그대로 잡힘.
        s = s or ""
        s = (
            s.replace("\u2018", "'")
            .replace("\u2019", "'")  # ‘ ’ → '
            .replace("\u201c", '"')
            .replace("\u201d", '"')
        )  # “ ” → "
        s = (
            s.replace("\u2219", "")
            .replace("\u00b7", "")  # ∙ · 가운뎃점류 제거
            .replace("\u2027", "")
        )
        return re.sub(r"\s+", "", s)

    for idx, (p_from, p_to, _) in enumerate(ranges, 1):
        print(f"[2/3] 파싱 {idx}/{len(ranges)} — p.{p_from}-{p_to} ...", flush=True)
        try:
            document = extract_pages(args.pdf, p_from, p_to, snapshot_dir=snapshot_dir)
            doc_norm = _norm(document)
            raw = call_llm(system_prompt, document, args.model)
            data = parse_json_strict(raw)
            result = ParseResult(**data)
            for rider in result.riders:
                key = (rider.name, rider.source.page)
                if key in seen:
                    continue
                seen.add(key)
                rider.verified = False
                all_riders.append(rider)
                w = rider.warnings()
                if w:
                    warnings.append((rider.name, w))
                # raw_text 원문 대조 — LLM이 인용을 변형했으면 경고 (인용 검증 신뢰성)
                rt = rider.source.raw_text
                if rt and _norm(rt) not in doc_norm:
                    quote_mismatch.append((rider.name, rider.source.page))
        except Exception as e:
            print(f"      ⚠️ 구간 p.{p_from}-{p_to} 실패: {str(e)[:80]}")
            failed.append((p_from, p_to, str(e)[:120]))
            continue
        time.sleep(1)  # API rate limit 여유

    # 3. 병합 저장
    merged = ParseResult(riders=all_riders)
    out_path = Path(args.out or ROOT / "data" / "parsed" / f"{stem}_전체.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(merged.model_dump_json(indent=2), encoding="utf-8")

    print(f"[3/3] 완료 — 보장 {len(all_riders)}개 → {out_path}")
    if warnings:
        print(f"      ℹ️ 비표준값 경고 {len(warnings)}건 (검수 시 정규화 — 데이터는 보존됨):")
        for name, ws in warnings[:10]:
            print(f"        · {name}: {'; '.join(ws)}")
        if len(warnings) > 10:
            print(f"        · ... 외 {len(warnings) - 10}건")
    if quote_mismatch:
        print(
            f"      ⚠️ raw_text 원문 불일치 {len(quote_mismatch)}건 (LLM이 인용을 변형 — 검수 시 원문으로 교체 필수):"
        )
        for name, pg in quote_mismatch[:10]:
            print(f"        · {name} (p.{pg})")
        if len(quote_mismatch) > 10:
            print(f"        · ... 외 {len(quote_mismatch) - 10}건")
    if failed:
        print(f"      ⚠️ 실패 구간 {len(failed)}개 (재시도 권장):")
        for p_from, p_to, err in failed:
            print(f"        p.{p_from}-{p_to}: {err}")
    print("      다음 단계: 검수 체크리스트로 대조 → verified 처리 → 적재 (검수: 담당자)")


if __name__ == "__main__":
    main()
