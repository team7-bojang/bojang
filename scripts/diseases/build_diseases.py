"""
build_diseases.py — 심평원 상병마스터 → /diseases/search 자동완성 테이블 전처리

용도:
    질병명 자동완성(SCR-03 상황 입력)에 쓸 diseases 테이블 원천 데이터 생성.
    심평원 상병마스터(KCD 8차)에서 3자리 표제어만 추려 깔끔한 검색 테이블로 가공.

사용법:
    python build_diseases.py 건강보험심사평가원_상병마스터_20250930.csv
    python build_diseases.py <원본.csv> --out-dir ./output

출력:
    diseases.csv  — kcd, name, search_text (Supabase import용, UTF-8 BOM)
    diseases.sql  — INSERT 문 + 테이블 생성 주석

전처리 결정 (왜 이렇게 했는지는 build_diseases_explore.ipynb 참고):
    1. 인코딩: 원본은 cp949 → UTF-8로 읽음
    2. 필터: 3자리 표제어만. 3자리 코드 행은 3,718행이며, 같은 코드의 별칭을
             search_text로 병합하면 최종 unique 2,085건. (47,798행 → 2,085건)
             말단 진단명(4~6자리)은 자동완성에 과함.
             약관이 보장을 3자리 범위(예: I60~I69 뇌혈관)로 정의하므로 매칭 단위와 정합.
    3. 컬럼: 10개 중 상병기호·한글명만 사용
    4. 정제: 한글명 중복 공백 정리
    5. 동의어: 같은 코드에 한글명 여러개면 첫 번째=대표명(name),
              나머지는 search_text에 합침 (화면은 깔끔, 검색은 넓게)
    6. 중복 제거: 같은 코드는 1건으로

데이터 출처:
    공공데이터포털 "건강보험심사평가원_상병마스터" (data.go.kr/data/15067467)
    로그인 없이 다운로드. 통계청 한국표준질병·사인분류(KCD) 기반.
"""
import sys
import csv
import re
import argparse
from collections import OrderedDict
from pathlib import Path

# 원본 컬럼명 (상병마스터 20250930 기준). 버전 바뀌어 헤더가 다르면 여기를 수정.
COL_CODE = "상병기호"
COL_NAME = "한글명"

# 자동완성 적재 기준: 3자리 KCD 표제어
CODE_LEN = 3

# 사용자용 별칭 (KCD 공식명 != 일상 표현) — search_text에만 병합, 화면 name은 공식명 유지
# 암(C코드)은 auto_cancer_alias()로 "X의 악성 신생물 → X암"을 자동 생성한다.
# 아래 수동 목록은 ① 자동이 놓치는 복합부위 암(간암·폐암 등)과 ② 비암 질병만 보강.
# 동의어 사전: KCD 제3권 색인(의학명) + 수동 일상어 2층 병합본.
# 출처/증거: merged_synonyms.csv (layer·source_page·raw_line 컬럼).
# 재생성: build_synonyms_from_index.py → merge_synonyms.py
from merged_synonyms import MANUAL_SYNONYMS
# 노이즈 수식어 — 부위명에 이게 있으면 자동 별칭 생성을 건너뜀(어색한 별칭 방지)
_CANCER_NOISE = ("기타", "상세불명", "부분", "부위불명", "및", ",")


def auto_cancer_alias(kcd, name):
    """C코드 '~의 악성 신생물' → 'X암' 자동 별칭. 복합/노이즈 부위는 None.

    예: '위의 악성 신생물' → '위암', '후두의 악성 신생물' → '후두암'.
    복합부위('간 및 간내 담관의...')나 노이즈('혀의 기타 및...')는 수동 목록으로 보강.
    """
    if not kcd.startswith("C"):
        return None
    m = re.match(r"^(.+?)의 악성 신생물$", name)
    if not m:
        return None
    site = m.group(1).strip()
    if any(n in site for n in _CANCER_NOISE):
        return None
    if len(site) > 6:          # 부위명이 너무 길면 복합부위로 보고 스킵
        return None
    return site + "암"


ENCODINGS = ("cp949", "euc-kr", "utf-8-sig", "utf-8")


def read_rows(path):
    """인코딩 자동 감지하며 CSV 읽기. (header, rows) 반환."""
    for enc in ENCODINGS:
        try:
            with open(path, encoding=enc, newline="") as f:
                reader = csv.reader(f)
                header = next(reader)
                rows = list(reader)
            print(f"[인코딩] {enc} 로 읽음")
            return header, rows
        except (UnicodeDecodeError, StopIteration):
            continue
    raise RuntimeError("CSV 인코딩을 읽지 못했습니다. ENCODINGS에 인코딩을 추가하세요.")


def build(header, rows):
    """3자리 표제어 추출 + 동의어 병합. [(kcd, name, search_text)] 반환."""
    idx = {h: n for n, h in enumerate(header)}
    if COL_CODE not in idx or COL_NAME not in idx:
        raise KeyError(
            f"필요 컬럼이 없습니다: {COL_CODE}, {COL_NAME} / 실제 헤더={header}"
        )
    ci, ni = idx[COL_CODE], idx[COL_NAME]

    rep = OrderedDict()   # code -> 대표 한글명
    synonyms = {}         # code -> [추가 한글명]
    for r in rows:
        if len(r) <= max(ci, ni):
            continue
        code = r[ci].strip()
        name = re.sub(r"\s+", " ", r[ni].strip())   # 중복 공백 정리
        if len(code) != CODE_LEN or not name:
            continue
        if code not in rep:
            rep[code] = name
        elif name != rep[code]:
            synonyms.setdefault(code, []).append(name)

    out = []
    for code, name in rep.items():
        syns = synonyms.get(code, [])           # 심평원 별칭(의학 이명)
        manual = MANUAL_SYNONYMS.get(code, [])  # 사용자 일상어 별칭(수동)
        auto = auto_cancer_alias(code, name)    # 암 별칭 자동 생성
        auto_list = [auto] if auto else []
        # search_text = 공식명 + 심평원 별칭 + 자동 암별칭 + 수동 별칭 (중복 제거, 순서 유지)
        terms = []
        for t in [name] + syns + auto_list + manual:
            if t and t not in terms:
                terms.append(t)
        search_text = " ".join(terms)
        out.append((code, name, search_text))   # name은 KCD 공식 표제어 유지
    return out


def write_csv(out, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kcd", "name", "search_text"])
        w.writerows(out)


def write_sql(out, path):
    q = lambda s: s.replace("'", "''")
    with open(path, "w", encoding="utf-8") as f:
        f.write("-- diseases 자동완성 테이블 (심평원 상병마스터, KCD 3자리 표제어)\n")
        f.write(f"-- 적재 {len(out)}건. 출처: data.go.kr/data/15067467\n")
        f.write("-- create table diseases (\n")
        f.write("--   kcd text primary key,\n")
        f.write("--   name text not null,\n")
        f.write("--   search_text text   -- 대표명+별칭, 자동완성 LIKE/trgm 검색용\n")
        f.write("-- );\n")
        f.write("-- create extension if not exists pg_trgm;\n")
        f.write("-- create index on diseases using gin (search_text gin_trgm_ops);\n")
        f.write("--\n")
        f.write("-- [검색 쿼리 예시] /diseases/search?q=뇌경색\n")
        f.write("-- 정렬: 진단코드 우선(R/Z 증상·기타코드는 뒤로) > 대표명 정확매칭 > search_text 별칭 단어 정확일치 > 대표명 앞부분 > 대표명 포함 > 짧은 이름.\n")
        f.write("-- (예: '당뇨' → E10/E11 당뇨병 계열이 R81 '당뇨'(증상코드)보다 위 / '뇌경색' → I63이 I65·I66보다 위)\n")
        f.write("-- select kcd, name from diseases\n")
        f.write("-- where search_text like '%' || :q || '%'\n")
        f.write("-- order by\n")
        f.write("--   (left(kcd,1) in ('R','Z')) asc,\n")
        f.write("--   (name = :q) desc,\n")
        f.write(
            "--   (search_text = :q or search_text like :q || ' %' or search_text like '% ' || :q || ' %' or search_text like '% ' || :q) desc,\n")
        f.write("--   (name like :q || '%') desc,\n")
        f.write("--   (name like '%' || :q || '%') desc,\n")
        f.write("--   length(name)\n")
        f.write("-- limit 10;\n\n")
        for code, name, st in out:
            f.write(
                f"insert into diseases (kcd, name, search_text) "
                f"values ('{code}', '{q(name)}', '{q(st)}');\n"
            )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="상병마스터 원본 CSV 경로")
    ap.add_argument("--out-dir", default=".", help="출력 폴더 (기본: 현재 폴더)")
    args = ap.parse_args()

    header, rows = read_rows(args.src)
    print(f"[원본] {len(rows):,}행, 컬럼 {len(header)}개")

    out = build(header, rows)
    print(f"[결과] 3자리 표제어 {len(out):,}건")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out, out_dir / "diseases.csv")
    write_sql(out, out_dir / "diseases.sql")
    print(f"[저장] {out_dir/'diseases.csv'}, {out_dir/'diseases.sql'}")


if __name__ == "__main__":
    main()
