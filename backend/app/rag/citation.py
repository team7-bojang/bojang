import re


def verify_quote(quote: str, raw_text: str) -> bool:
    """인용문이 원문에 포함되는지 검증합니다.

    줄바꿈이나 공백 차이로 매칭이 실패하지 않도록 특수문자와 공백을 제거하고 부분 대조합니다.
    """
    if not quote or not raw_text:
        return False

    # 텍스트 정규화: 특수문자, 문장부호, 공백 제거
    def clean(text):
        text = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z]", "", text)  # 한글, 영문, 숫자만 남김
        return text.strip()

    clean_quote = clean(quote)
    clean_raw = clean(raw_text)

    if not clean_quote:
        return False

    return clean_quote in clean_raw
