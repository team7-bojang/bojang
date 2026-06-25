"""진료비 세부산정내역서 파싱(app/parsing/medical_statement.py) 및
POST /cases/{case_id}/medical-detail-statement 계약 테스트.
"""

import io
import json
from types import SimpleNamespace

from PIL import Image

from app.config import settings
from app.db import get_client
from app.parsing import medical_statement
from app.parsing.medical_statement import (
    parse_medical_statement,
    parse_medical_statement_image,
    parse_medical_statement_text,
)
from app.schemas.case import ExtractedMedicalInfo
from app.services import case_service


def _tiny_png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), color=(255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


class _FakeOpenAI:
    """openai.OpenAI 클라이언트를 흉내내는 테스트 더블 — chat.completions.create()만 지원."""

    def __init__(self, response_content: str):
        self._response_content = response_content
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._response_content))])


OWNER_ID = "00000000-0000-0000-0000-000000000000"  # require_auth 디버그 폴백 사용자

# 실제 "진료비 세부산정내역" 양식(외래, 도수치료-A 비급여 90,000원 포함)을 그대로 옮긴 본문.
# pdfplumber.page.extract_text() 가 표 한 행을 한 줄로 이어 붙이는 레이아웃을 가정한다.
_SAMPLE_TEXT = """\
환자등록번호 환자성명 진료기간 병실 환자구분 비고
1928 진미경 2026-06-23 ~ 2026-06-23 외래 국민건강보험

항목 일자 코드 명칭 금액 횟수 일수 총액 본인부담금 공단부담금 전액본인부담 비급여
진찰료 2026.06.23 AA254010 재진진찰료-의원/보건의료원 내 의과(야간) 16,180 1 1 16,180 4,854 11,326 0 0
재활물리치료료 2026.06.23 MM010 표층열치료 1,010 1 1 1,010 303 707 0 0
재활물리치료료 2026.06.23 MM085 재활저출력레이저치료[1일당] 6,710 1 1 6,710 2,013 4,697 0 0
처치및수술료 2026.06.23 MANUAL-A 도수치료-A 90,000 1 1 90,000 0 0 0 90,000

계 113,900 7,170 16,730 0 90,000
끝수처리조정금액 0 -70 70 0 0
합계 113,900 7,100 16,800 0 90,000

요양기관 명칭 웰컴365신경외과의원 대표자 정재환
"""


def test_parse_medical_statement_text_extracts_items_and_summary():
    parsed = parse_medical_statement_text(_SAMPLE_TEXT)

    assert parsed["patient_name"] == "진미경"
    assert parsed["hospital_name"] == "웰컴365신경외과의원"
    assert parsed["period_start"] == "2026-06-23"
    assert parsed["period_end"] == "2026-06-23"
    assert parsed["ward"] == "외래"

    assert len(parsed["items"]) == 4
    manual_item = next(i for i in parsed["items"] if i["code"] == "MANUAL-A")
    assert manual_item["name"] == "도수치료-A"
    assert manual_item["total"] == 90000
    assert manual_item["non_covered"] == 90000

    physical_item = next(i for i in parsed["items"] if i["code"] == "MM010")
    assert physical_item["non_covered"] == 0


def test_parse_medical_statement_text_uses_final_settlement_row_not_subtotal():
    parsed = parse_medical_statement_text(_SAMPLE_TEXT)

    # "계"(조정 전 소계)가 아닌 "합계"(끝수처리 반영 최종값)를 사용해야 한다.
    assert parsed["summary"] == {
        "total_amount": 113900,
        "patient_paid_amount": 7100,
        "nhis_paid_amount": 16800,
        "full_self_pay_amount": 0,
        "non_covered_amount": 90000,
    }


def test_parse_medical_statement_text_uses_single_total_row_when_no_final_total():
    text = """\
환자등록번호 환자성명 진료기간 병실 환자구분 비고
1928 진미경 2026-06-23 ~ 2026-06-23 외래 국민건강보험
진찰료 2026.06.23 AA254010 재진진찰료 16,180 1 1 16,180 4,854 11,326 0 0
계 16,180 4,854 11,326 0 0
"""

    parsed = parse_medical_statement_text(text)

    assert parsed["summary"] == {
        "total_amount": 16180,
        "patient_paid_amount": 4854,
        "nhis_paid_amount": 11326,
        "full_self_pay_amount": 0,
        "non_covered_amount": 0,
    }


def test_parse_medical_statement_text_returns_empty_summary_when_no_match():
    parsed = parse_medical_statement_text("관련 없는 텍스트입니다.")

    assert parsed["items"] == []
    assert parsed["summary"] == {}


def test_extracted_medical_info_schema_documents_visit_dates_array():
    schema = ExtractedMedicalInfo.model_json_schema()

    assert "visit_date" not in schema["properties"]
    assert schema["properties"]["visit_dates"] == {
        "default": [],
        "items": {"type": "string"},
        "title": "Visit Dates",
        "type": "array",
    }


def test_parse_medical_statement_falls_back_to_tables_when_text_layout_breaks(monkeypatch):
    # extract_text() 가 표를 깨뜨려 항목을 못 찾는 상황을 가정 — extract_tables() 셀로 재시도해야 한다.
    table = [
        ["1928", "진미경", "2026-06-23 ~ 2026-06-23", "외래", "국민건강보험"],
        [
            "진찰료",
            "2026.06.23",
            "AA254010",
            "재진진찰료-의원",
            "16,180",
            "1",
            "1",
            "16,180",
            "4,854",
            "11,326",
            "0",
            "0",
        ],
        ["합계", "16,180", "4,854", "11,326", "0", "0"],
        ["요양기관 명칭", "웰컴365신경외과의원"],
    ]
    pages = [{"page": 1, "text": "표가 깨져서 못 읽는 텍스트", "tables": [table]}]
    monkeypatch.setattr(medical_statement, "extract_pages", lambda pdf_bytes: pages)

    parsed = parse_medical_statement(b"%PDF-1.4 dummy")

    assert parsed["patient_name"] == "진미경"
    assert parsed["hospital_name"] == "웰컴365신경외과의원"
    assert len(parsed["items"]) == 1
    assert parsed["items"][0]["code"] == "AA254010"
    assert parsed["summary"]["patient_paid_amount"] == 4854


def test_parse_medical_statement_image_returns_empty_without_api_key(monkeypatch):
    # API 키 미설정 시 추측하지 않고 빈 결과를 반환해야 한다(잘못된 금액 환각 방지).
    monkeypatch.setattr(settings, "openai_api_key", "")

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["items"] == []
    assert parsed["summary"] == {}


def test_parse_medical_statement_image_normalizes_vision_response(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": "웰컴365신경외과의원",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "처치및수술료",
                    "code": "MANUAL-A",
                    "name": "도수치료-A",
                    "count": 1,
                    "days": 1,
                    "total": "90,000",
                    "non_covered": 90000,
                }
            ],
            "summary": {
                "total_amount": 90000,
                "patient_paid_amount": 0,
                "nhis_paid_amount": 0,
                "full_self_pay_amount": 0,
                "non_covered_amount": 90000,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["patient_name"] == "진미경"
    assert parsed["items"][0]["total"] == 90000
    assert parsed["summary"]["non_covered_amount"] == 90000


def test_parse_medical_statement_image_corrects_known_item_names_by_code(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": "월곶365신경외과의원",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "재활물리치료료",
                    "code": "MM010",
                    "name": "표준물리치료",
                    "count": 1,
                    "days": 1,
                    "total": "1,010",
                    "non_covered": 0,
                },
                {
                    "category": "재활물리치료료",
                    "code": "MM085",
                    "name": "재활물리치료이용[1일]",
                    "count": 1,
                    "days": 1,
                    "total": "6,710",
                    "non_covered": 0,
                },
            ],
            "summary": {
                "total_amount": 90000,
                "patient_paid_amount": 90000,
                "nhis_paid_amount": 0,
                "full_self_pay_amount": 0,
                "non_covered_amount": 0,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert [item["name"] for item in parsed["items"]] == [
        "표층열치료",
        "재활저출력레이저치료[1일당]",
    ]


def test_parse_medical_statement_image_returns_empty_on_llm_failure(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")

    def _raise(**kwargs):
        raise RuntimeError("API down")

    monkeypatch.setattr(
        "openai.OpenAI",
        lambda api_key=None: SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=_raise))),
    )

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["items"] == []
    assert parsed["summary"] == {}


def test_parse_medical_statement_image_drops_summary_when_amount_missing(monkeypatch):
    # patient_paid_amount 를 못 읽어 null로 온 경우 0으로 둔갑시키지 않고 summary 전체를 버려야 한다.
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": "웰컴365신경외과의원",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "처치및수술료",
                    "code": "MANUAL-A",
                    "name": "도수치료-A",
                    "count": 1,
                    "days": 1,
                    "total": 90000,
                    "non_covered": 90000,
                }
            ],
            "summary": {
                "total_amount": 113900,
                "patient_paid_amount": None,
                "nhis_paid_amount": 16800,
                "full_self_pay_amount": 0,
                "non_covered_amount": 90000,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["summary"] == {}


def test_parse_medical_statement_image_keeps_real_zero_amount(monkeypatch):
    # full_self_pay_amount=0 처럼 "키가 있고 실제 값이 0"인 경우는 정상적으로 0으로 인정해야 한다.
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": "웰컴365신경외과의원",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "처치및수술료",
                    "code": "MANUAL-A",
                    "name": "도수치료-A",
                    "count": 1,
                    "days": 1,
                    "total": 90000,
                    "non_covered": 0,
                }
            ],
            "summary": {
                "total_amount": 90000,
                "patient_paid_amount": 90000,
                "nhis_paid_amount": 0,
                "full_self_pay_amount": 0,
                "non_covered_amount": 0,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["summary"]["full_self_pay_amount"] == 0
    assert parsed["items"][0]["non_covered"] == 0


def test_parse_medical_statement_image_keeps_summary_even_if_inconsistent_with_items(monkeypatch):
    # Vision이 항목 금액 열을 잘못 읽어 items 합계와 summary가 안 맞아도, 값이 전부 채워져
    # 있으면 그대로 저장한다 — 틀린 값은 사용자가 직접 화면에서 고치는 쪽으로 처리한다.
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": None,
            "disease_name": "허리디스크",
            "disease_kcd": "M51",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "진찰료",
                    "code": "AA254010",
                    "name": "재진진찰료",
                    "count": 1,
                    "days": 1,
                    "total": 16180,
                    "non_covered": 0,
                },
                {
                    "category": "재활물리치료료",
                    "code": "MM010",
                    "name": "표층열치료",
                    "count": 1,
                    "days": 1,
                    "total": 1010,
                    "non_covered": 0,
                },
                {
                    "category": "재활물리치료료",
                    "code": "MM085",
                    "name": "재활저출력레이저치료[1일당]",
                    "count": 1,
                    "days": 1,
                    "total": 2013,
                    "non_covered": 0,
                },
                {
                    "category": "처치및수술료",
                    "code": "MANUAL-A",
                    "name": "도수치료-A",
                    "count": 1,
                    "days": 1,
                    "total": 90000,
                    "non_covered": 90000,
                },
            ],
            "summary": {
                "total_amount": 113203,
                "patient_paid_amount": 0,
                "nhis_paid_amount": 0,
                "full_self_pay_amount": 0,
                "non_covered_amount": 90000,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert parsed["summary"] == {
        "total_amount": 113203,
        "patient_paid_amount": 0,
        "nhis_paid_amount": 0,
        "full_self_pay_amount": 0,
        "non_covered_amount": 90000,
    }


def test_parse_medical_statement_image_drops_item_with_missing_amount(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-test-dummy")
    vision_json = json.dumps(
        {
            "patient_name": "진미경",
            "hospital_name": "웰컴365신경외과의원",
            "period_start": "2026-06-23",
            "period_end": "2026-06-23",
            "ward": "외래",
            "items": [
                {
                    "category": "처치및수술료",
                    "code": "MANUAL-A",
                    "name": "도수치료-A",
                    "count": 1,
                    "days": 1,
                    "total": None,
                    "non_covered": 90000,
                },
                {
                    "category": "진찰료",
                    "code": "AA254010",
                    "name": "재진진찰료",
                    "count": 1,
                    "days": 1,
                    "total": 16180,
                    "non_covered": 0,
                },
            ],
            "summary": {
                "total_amount": 113900,
                "patient_paid_amount": 7100,
                "nhis_paid_amount": 16800,
                "full_self_pay_amount": 0,
                "non_covered_amount": 90000,
            },
        }
    )
    monkeypatch.setattr("openai.OpenAI", lambda api_key=None: _FakeOpenAI(vision_json))

    parsed = parse_medical_statement_image(_tiny_png_bytes())

    assert len(parsed["items"]) == 1
    assert parsed["items"][0]["code"] == "AA254010"


def _create_case(**overrides) -> str:
    db = get_client()
    case = {
        "user_id": OWNER_ID,
        "service_type": "CASE1",
        "disease_name": "허리디스크",
        "disease_kcd": "M511",
        **overrides,
    }
    res = db.table("cases").insert(case).execute()
    data = res.data
    if isinstance(data, list):
        return data[0]["id"]
    return data["id"]


def _fake_parsed_statement(**overrides) -> dict:
    parsed = {
        "patient_name": "진미경",
        "hospital_name": "웰컴365신경외과의원",
        "period_start": "2026-06-23",
        "period_end": "2026-06-23",
        "ward": "외래",
        "items": [
            {
                "category": "진찰료",
                "code": "AA254010",
                "name": "재진진찰료-의원",
                "count": 1,
                "days": 1,
                "total": 16180,
                "non_covered": 0,
            },
            {
                "category": "재활물리치료료",
                "code": "MM010",
                "name": "표층열치료",
                "count": 1,
                "days": 1,
                "total": 1010,
                "non_covered": 0,
            },
            {
                "category": "처치및수술료",
                "code": "MANUAL-A",
                "name": "도수치료-A",
                "count": 1,
                "days": 1,
                "total": 90000,
                "non_covered": 90000,
            },
        ],
        "summary": {
            "total_amount": 113900,
            "patient_paid_amount": 7100,
            "nhis_paid_amount": 16800,
            "full_self_pay_amount": 0,
            "non_covered_amount": 90000,
        },
    }
    parsed.update(overrides)
    return parsed


def test_save_medical_detail_statement_updates_case_from_parsed_pdf(monkeypatch):
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement", lambda pdf_bytes: _fake_parsed_statement())

    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    info = result["extracted_medical_info"]
    assert info["payment_amount"] == 7100 + 90000
    assert info["full_self_pay_amount"] == 0
    assert info["is_outpatient"] is True
    assert info["is_inpatient"] is False
    assert info["visit_dates"] == ["2026-06-23"]
    assert info["hospital_name"] == "웰컴365신경외과의원"
    assert "MANUAL_THERAPY" in info["treatment_items"]
    assert "PHYSICAL_THERAPY" in info["treatment_items"]

    case = get_client().table("cases").select("*").eq("id", case_id).execute().data[0]
    assert case["payment_amount"] == 97100
    assert case["visit_dates"] == ["2026-06-23"]


def test_save_medical_detail_statement_response_does_not_fallback_to_case_disease(monkeypatch):
    case_id = _create_case(disease_name="허리디스크", disease_kcd="M511")
    monkeypatch.setattr(
        case_service,
        "parse_medical_statement",
        lambda pdf_bytes: _fake_parsed_statement(disease_name=None, disease_kcd=None),
    )

    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    info = result["extracted_medical_info"]
    assert info["disease_name"] is None
    assert info["disease_kcd"] is None

    case = get_client().table("cases").select("*").eq("id", case_id).execute().data[0]
    assert case["disease_name"] == "허리디스크"
    assert case["disease_kcd"] == "M511"


def test_save_medical_detail_statement_rejects_second_upload(monkeypatch):
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement", lambda pdf_bytes: _fake_parsed_statement())

    case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    try:
        case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")
        raise AssertionError("두 번째 업로드는 거부되어야 합니다.")
    except ValueError as e:
        assert "1건" in str(e)


def test_save_medical_detail_statement_rejects_case2():
    case_id = _create_case(service_type="CASE2")

    try:
        case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")
        raise AssertionError("CASE2는 거부되어야 합니다.")
    except ValueError as e:
        assert "CASE2" in str(e)


def test_save_medical_detail_statement_checks_ownership_before_case2():
    # 소유권 체크가 CASE2 체크보다 먼저 실행되어야 한다(서비스 타입 추론으로 인한 정보 노출 방지).
    other_user_id = "11111111-1111-1111-1111-111111111111"
    case_id = _create_case(service_type="CASE2")

    try:
        case_service.save_medical_detail_statement(other_user_id, case_id, b"%PDF-1.4 dummy")
        raise AssertionError("소유자가 아니면 거부되어야 합니다.")
    except case_service.ForbiddenError as e:
        assert "다른 사용자" in str(e)


def test_save_medical_detail_statement_allows_upload_even_if_visit_dates_set_by_payment(monkeypatch):
    # visit_dates 는 결제내역 입력에서도 채워지는 공용 필드라, 이것만으로 "이미 업로드됨"을
    # 판단하면 결제내역을 먼저 입력한 정상 케이스의 첫 업로드가 막힌다.
    case_id = _create_case(visit_dates=["2026-06-20"])
    monkeypatch.setattr(case_service, "parse_medical_statement", lambda pdf_bytes: _fake_parsed_statement())

    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    assert result["extracted_medical_info"]["payment_amount"] == 7100 + 90000


def test_save_medical_detail_statement_includes_full_self_pay_in_payment_amount(monkeypatch):
    parsed = _fake_parsed_statement(
        summary={
            "total_amount": 133900,
            "patient_paid_amount": 7100,
            "nhis_paid_amount": 16800,
            "full_self_pay_amount": 20000,
            "non_covered_amount": 90000,
        }
    )
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement", lambda pdf_bytes: parsed)

    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    assert result["extracted_medical_info"]["payment_amount"] == 7100 + 20000 + 90000
    assert result["extracted_medical_info"]["full_self_pay_amount"] == 20000


def test_save_medical_detail_statement_rejects_non_pdf_bytes():
    case_id = _create_case()

    try:
        case_service.save_medical_detail_statement(OWNER_ID, case_id, b"not a pdf")
        raise AssertionError("PDF/이미지 매직바이트가 없으면 거부되어야 합니다.")
    except ValueError as e:
        assert "PDF" in str(e)


def test_save_medical_detail_statement_routes_jpeg_to_vision_parser(monkeypatch):
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement_image", lambda file_bytes: _fake_parsed_statement())

    def _fail_if_called(pdf_bytes):
        raise AssertionError("JPEG 업로드는 PDF 파서를 호출하면 안 됩니다.")

    monkeypatch.setattr(case_service, "parse_medical_statement", _fail_if_called)

    jpeg_magic_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 16
    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, jpeg_magic_bytes)

    assert result["extracted_medical_info"]["payment_amount"] == 7100 + 90000


def test_save_medical_detail_statement_routes_png_to_vision_parser(monkeypatch):
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement_image", lambda file_bytes: _fake_parsed_statement())

    png_magic_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, png_magic_bytes)

    assert result["extracted_medical_info"]["hospital_name"] == "웰컴365신경외과의원"


def test_save_medical_detail_statement_rejects_unrecognized_image(monkeypatch):
    case_id = _create_case()
    # 사진이지만 Vision LLM이 인식하지 못한 경우(빈 결과) — 더 선명한 사진을 요청해야 한다.
    monkeypatch.setattr(
        case_service,
        "parse_medical_statement_image",
        lambda file_bytes: {"items": [], "summary": {}},
    )

    jpeg_magic_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 16
    try:
        case_service.save_medical_detail_statement(OWNER_ID, case_id, jpeg_magic_bytes)
        raise AssertionError("인식 실패 시 거부되어야 합니다.")
    except ValueError as e:
        assert "사진" in str(e) or "PDF" in str(e)


def test_save_medical_detail_statement_accepts_items_with_unverified_summary(monkeypatch):
    # items는 읽었지만 summary 산식 검증에 실패해 비어 있는 경우 — 업로드 자체는 거부하지 않고
    # payment_amount 등 합계 관련 필드만 None으로 비워서, 사용자가 문자/카드내역 입력으로
    # 직접 채우도록 유도해야 한다(전체 재업로드를 강제하지 않음).
    case_id = _create_case()
    monkeypatch.setattr(
        case_service,
        "parse_medical_statement",
        lambda pdf_bytes: _fake_parsed_statement(summary={}),
    )

    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, b"%PDF-1.4 dummy")

    info = result["extracted_medical_info"]
    assert len(info["item_details"]) == 3
    assert info["payment_amount"] is None
    assert info["total_amount"] is None
    assert info["patient_paid_amount"] is None
    assert info["nhis_paid_amount"] is None
    assert info["full_self_pay_amount"] is None
    assert info["non_covered_amount"] is None
    assert result["next_question"]["question_id"] == "input_method"

    case = get_client().table("cases").select("*").eq("id", case_id).execute().data[0]
    assert case["payment_amount"] is None
    assert case["medical_statement_uploaded_at"] is not None


def test_save_medical_detail_statement_ignores_unparseable_vision_date(monkeypatch):
    # Vision LLM이 날짜를 YYYY-MM-DD 형식으로 못 맞춰도(예: "내일") 500이 아니라
    # 그 날짜만 누락 처리하고 나머지는 정상 처리되어야 한다.
    case_id = _create_case()
    monkeypatch.setattr(
        case_service,
        "parse_medical_statement_image",
        lambda file_bytes: _fake_parsed_statement(ward="6인실", period_start="내일", period_end="모름"),
    )

    jpeg_magic_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 16
    result = case_service.save_medical_detail_statement(OWNER_ID, case_id, jpeg_magic_bytes)

    info = result["extracted_medical_info"]
    assert info["is_inpatient"] is True
    assert info["visit_dates"] == []  # 인식 못 한 날짜는 누락 처리되어야 한다

    case = get_client().table("cases").select("*").eq("id", case_id).execute().data[0]
    assert case["admission_days_current"] == 14  # 날짜 기반 계산 실패 시 기본값으로 폴백


def test_post_medical_detail_statement_endpoint_requires_file(client):
    case_id = _create_case()

    res = client.post(f"/api/v1/cases/{case_id}/medical-detail-statement", data={})

    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "validation_error"


def test_post_medical_detail_statement_endpoint_accepts_file(client, monkeypatch):
    case_id = _create_case()
    monkeypatch.setattr(case_service, "parse_medical_statement", lambda pdf_bytes: _fake_parsed_statement())

    res = client.post(
        f"/api/v1/cases/{case_id}/medical-detail-statement",
        data={"file": (io.BytesIO(b"%PDF-1.4 dummy"), "statement.pdf")},
        content_type="multipart/form-data",
    )

    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["extracted_medical_info"]["payment_amount"] == 97100
