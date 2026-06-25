"""pdfplumber 기반 페이지별 텍스트·표 추출 (페이지 번호 보존)."""

from __future__ import annotations

import io

import pdfplumber


def extract_pages(pdf_bytes: bytes) -> list[dict]:
    """PDF 바이트에서 페이지별 텍스트와 표를 추출한다.

    반환: [{"page": 1, "text": "...", "tables": [[[cell, ...], ...], ...]}, ...]
    """
    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            pages.append(
                {
                    "page": i,
                    "text": page.extract_text() or "",
                    "tables": page.extract_tables() or [],
                }
            )
    return pages
