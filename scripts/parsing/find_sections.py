"""약관 PDF에서 파싱 후보 구간 자동 탐색 (워크플로 2단계 자동화).

키워드(보장명 + '보험금의 지급사유')가 함께 등장하는 페이지를 찾아
parse_rider.py에 넣을 --pages 구간을 제안한다.

사용법:
  python find_sections.py 약관.pdf
  python find_sections.py 약관.pdf --keywords 입원일당 골절 암진단
  python find_sections.py 약관.pdf --all-hits   # 트리거 없이 키워드 등장 페이지 전부

출력 예:
  [후보 1] p.60-61   질병입원일당  ← python parse_rider.py 약관.pdf --pages 60-61
"""

import argparse
import re
import sys
from pathlib import Path

import pdfplumber

DEFAULT_KEYWORDS = [
    # 정액 보장
    "입원일당",
    "수술비",
    "진단비",
    "진단자금",
    "골절",
    "입원급여금",
    "수술급여금",
    # 실손·통원·특정 치료 (놓치기 쉬운 보장)
    "실손의료비",
    "통원",
    "치료비",
    "항암",
    "표적",
    "방사선",
    "약물치료",
    "도수",
    "체외충격파",
    "자기공명",
    "MRI",
    "깁스",
    "부목",
    "물리치료",
    "재활",
]
TRIGGER = "보험금의 지급사유"  # 본문 시작 신호 — 목차·요약서 페이지를 걸러냄


def clean(t: str) -> str:
    return (t or "").replace("\x00", " ")


def scan(pdf_path: str, keywords: list[str], require_trigger: bool, full: bool = False):
    """후보 페이지 탐색.

    full=True: 키워드 무시, '보험금의 지급사유'가 있는 모든 페이지를 후보로
      → 통원·도수·항암 등 키워드 목록에 없는 보장도 빠짐없이 잡음 (전량 파싱용)
    full=False: 키워드 + (require_trigger 시) 지급사유 동반 페이지만 (빠름)
    """
    hits = []
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            text = clean(page.extract_text() or "")
            if full:
                if TRIGGER in text:
                    # 어떤 보장인지 힌트만 수집 (구간 라벨용, 매칭 없어도 통과)
                    matched = [k for k in keywords if k in text] or ["지급사유"]
                    hits.append((i, matched))
            else:
                matched = [k for k in keywords if k in text]
                if matched and (not require_trigger or TRIGGER in text):
                    hits.append((i, matched))
            if i % 100 == 0:
                print(f"  ...{i}/{total} 페이지 스캔", file=sys.stderr)
    return hits


def group_ranges(hits, gap=1):
    """인접 페이지(간격 gap 이하)를 하나의 후보 구간으로 병합."""
    ranges = []
    for page, kws in hits:
        if ranges and page - ranges[-1][1] <= gap:
            ranges[-1][1] = page
            ranges[-1][2] |= set(kws)
        else:
            ranges.append([page, page, set(kws)])
    return ranges


# 특약 제목 패턴 (두 가지를 OR로 — 약관 레이아웃 변동에 강건):
#  A) "...이름(비갱신형/갱신형)" — 이름 직후 갱신구분이 붙는 일반형
#  B) "번호 이름+보장접미사" — 줄바꿈/중간괄호로 (비갱신형)이 떨어진 경우 (예: p.97 뇌혈관입원일당)
_SUFFIX = (
    r"(?:입원일당|중환자실입원일당|진단비|진단자금|수술비|치료비|"
    r"급여금|입원비|통원비|보험금|사망|위로금|연금|호스피스)"
)
TITLE_PAT = re.compile(r"(\d{1,3})\s+([가-힣][가-힣A-Za-z0-9·Ⅰ-Ⅹ()\s]*?)\s*\((?:비갱신형|갱신형)")
TITLE_PAT_SUFFIX = re.compile(r"(\d{1,3})\s+([가-힣][가-힣A-Za-zⅠ-Ⅹ·]*?" + _SUFFIX + r")")
# C) "[번호.] (무배당) (비)갱신형 이름+(보장|특별약관)" — 갱신구분이 이름 앞에 오는 어순
#    (메리츠 등 손보 상해약관). 이름 안 공백/괄호/로마숫자 허용, '보장'·'특별약관'으로 종료.
#    DB식 "이름(조건)"은 '갱신형' 선두가 없어 여기 안 걸리고 기존 패턴이 담당 → 회귀 안전.
TITLE_PAT_RENEWAL = re.compile(
    r"(?:(\d{1,3})\.\s*)?(?:무배당\s*)?"
    r"((?:비)?갱신형\s+[가-힣A-Za-z0-9·Ⅰ-Ⅹ()\[\]%\s]+?(?:보장|특별약관))"
)


# 보장이 아닌 제도성·행정성 특약 (riders에서 제외 — 약관마다 이름 유사)
NON_COVERAGE_TITLES = [
    "선지급",
    "전자서명",
    "자동갱신",
    "장애인전용",
    "장애인전환",
    "단체취급",
    "보험료자동",
    "보험료 자동",
    "신용카드",
    "지정대리청구",
    "지정대리 청구",
    "부담보",
    "보장제한부",
    "특정신체부위",
    "특정 신체부위",
    "이륜자동차",
    "전환",
    "제도성",
    "계약전환",
    "연금전환",
]


def _is_non_coverage(name: str) -> bool:
    return any(kw in name for kw in NON_COVERAGE_TITLES)


def split_by_rider_title(
    pdf_path: str, max_pages_per_section: int = 4, drop_non_coverage: bool = True
):
    """특약 제목을 경계로 구간을 자른다 (전량 파싱의 누락 방지).

    한 특약 = [제목 페이지 ~ 다음 특약 제목 직전], 단 max_pages로 상한.
    같은 페이지에 여러 특약 제목이 있어도 모두 보존한다(번호 기준 중복 제거).
    제도성 특약(선지급·자동갱신 등)은 drop_non_coverage 시 제외.
    제목이 안 잡히는 약관(생보 통합약관 등)에서는 빈 리스트 반환 → 호출부에서 폴백.
    """
    titles = []  # (page, num, name)
    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        page_has_trigger = {}
        for i, page in enumerate(pdf.pages, start=1):
            text = clean(page.extract_text() or "")
            page_has_trigger[i] = TRIGGER in text
            for m in TITLE_PAT.finditer(text):
                titles.append((i, m.group(1), m.group(2).strip()))
            for m in TITLE_PAT_SUFFIX.finditer(text):
                titles.append((i, m.group(1), m.group(2).strip()))
            for m in TITLE_PAT_RENEWAL.finditer(text):
                # 번호가 없을 수 있으므로(갱신형 선두) group(1)이 None이면 빈 문자열
                titles.append((i, m.group(1) or "", m.group(2).strip()))
            if i % 100 == 0:
                print(f"  ...{i}/{total} 제목 스캔", file=sys.stderr)

    if not titles:
        return []

    # 요약 페이지 제외: 제목이 있어도 같은 페이지(또는 다음 페이지)에 지급사유가 없으면
    # 상품요약의 보장 목록일 가능성 — 진짜 본문 제목만 남긴다.
    real_titles = []
    for pg, num, name in titles:
        if page_has_trigger.get(pg) or page_has_trigger.get(pg + 1):
            real_titles.append((pg, num, name))
    if real_titles:
        titles = real_titles

    # 중복 제거: 번호만 보면 장이 바뀌어 번호가 재시작할 때 오류 → (num, name) 조합 사용.
    # 같은 (num, name)이 여러 번(머리말 반복)이면 첫 등장만.
    seen = set()
    uniq = []
    for pg, num, name in titles:
        key = (num, name)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((pg, num, name))

    # 페이지 오름차순 정렬
    uniq.sort(key=lambda x: x[0])

    # 잘린 제목 오탐 제거: 어떤 제목이 직전 진짜 제목의 '꼬리'(끝부분 substring)이고
    # 바로 다음 페이지(±1)에 나타나면, PDF 추출이 제목을 두 페이지로 쪼갠 잔해로 본다.
    # 예: p.98 "허혈심장질환입원일당" → p.99 "혈심장질환입원일당" (앞글자 잘림)
    cleaned_titles = []
    for pg, num, name in uniq:
        is_fragment = False
        if cleaned_titles:
            prev_pg, _, prev_name = cleaned_titles[-1]
            # 직전 제목 이름이 현재 이름으로 끝나거나(꼬리), 현재가 직전의 부분이고 인접 페이지
            if 0 <= pg - prev_pg <= 1 and len(name) >= 4 and prev_name.endswith(name):
                is_fragment = True
        if not is_fragment:
            cleaned_titles.append((pg, num, name))
    uniq = cleaned_titles

    ranges = []
    for idx, (pg, num, name) in enumerate(uniq):
        if drop_non_coverage and _is_non_coverage(name):
            continue
        # 시작 페이지가 PDF 범위를 넘으면 건너뜀 (색인·잔여 오탐 방어)
        if pg > total:
            continue
        # 다음 특약(제도성 포함)의 시작 페이지를 경계로
        next_pg = uniq[idx + 1][0] if idx + 1 < len(uniq) else pg + max_pages_per_section
        end = min(next_pg - 1, pg + max_pages_per_section - 1)
        end = max(end, pg)
        end = min(end, total)  # PDF 마지막 페이지를 넘지 않도록 clamp
        ranges.append([pg, end, {name}])

    # 안전망: '보험금의 지급사유'가 있는데 어떤 구간에도 안 들어간 페이지를 보강.
    # (제목 인식이 실패한 보장의 누락 방지 — 지적된 p.46·p.79~83·p.98 등)
    # 단, 보장 키워드가 전혀 없는 페이지(순수 공통조항·요약)는 제외해 과포함 억제.
    covered = set()
    for f, t, _ in ranges:
        covered.update(range(f, t + 1))
    with pdfplumber.open(pdf_path) as pdf:
        uncovered = []
        for i, page in enumerate(pdf.pages, start=1):
            if i in covered or not page_has_trigger.get(i):
                continue
            text = clean(page.extract_text() or "")
            # 보장 키워드가 하나라도 있어야 보강 (없으면 공통조항일 확률 높음)
            if not any(k in text for k in DEFAULT_KEYWORDS):
                continue
            # 별표·부표 페이지는 보장이 아님 (분류표·지급예시표 등) — 명확히 제외
            head = text.lstrip()[:20]
            if head.startswith("【별표") or head.startswith("[별표") or "별표" in head[:6]:
                continue
            uncovered.append(i)
    # 연속된 미커버 페이지를 구간으로 묶어 추가
    if uncovered:
        s = uncovered[0]
        prev = uncovered[0]
        for pg in uncovered[1:] + [None]:
            if pg is not None and pg - prev == 1 and pg - s < max_pages_per_section:
                prev = pg
                continue
            ranges.append([s, prev, {"(지급사유 보강)"}])
            if pg is not None:
                s = prev = pg
    ranges.sort(key=lambda x: x[0])

    # 겹침·중복 병합: 두 제목 패턴이 같은 특약을 다르게 잡거나(이름 길이 차),
    # 구간이 겹치면 하나로 합쳐 LLM 중복 호출·중복 파싱 방지.
    merged = []
    for f, t, names in ranges:
        if merged and f <= merged[-1][1]:  # 직전 구간과 겹침
            merged[-1][1] = max(merged[-1][1], t)
            merged[-1][2] |= names
        else:
            merged.append([f, t, set(names)])
    # 같은 시작 페이지 중복 제거(병합으로 대부분 해소되나 안전차원)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    ap.add_argument(
        "--all-hits",
        action="store_true",
        help="'보험금의 지급사유' 동반 조건 없이 전부 표시 (목차·요약 포함)",
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="키워드 무시, '보험금의 지급사유' 있는 모든 페이지 탐색 (빠짐없이, 전량 파싱용)",
    )
    args = ap.parse_args()

    hits = scan(args.pdf, args.keywords, require_trigger=not args.all_hits, full=args.full)
    if not hits:
        print("후보 없음 — --all-hits 또는 키워드를 바꿔 재시도하세요.")
        return

    pdf_name = Path(args.pdf).name
    print(f"\n파싱 후보 구간 ({pdf_name}, 키워드: {', '.join(args.keywords)})\n")
    for n, (p_from, p_to, kws) in enumerate(group_ranges(hits), 1):
        rng = f"{p_from}-{p_to}"
        print(
            f"[후보 {n:>2}] p.{rng:<9} {', '.join(sorted(kws)):<30}"
            f' ← python parse_rider.py "{pdf_name}" --pages {rng}'
        )
    print("\n※ 후보는 '보험금의 지급사유' 문구가 있는 본문 페이지만 표시 (목차·요약서 제외).")
    print("※ 구간이 보장 2개 이상을 포함하면 그대로 넣어도 됨 — 출력 JSON에 여러 rider로 분리됨.")


if __name__ == "__main__":
    main()
