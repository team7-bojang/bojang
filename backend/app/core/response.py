"""공통 응답 봉투 (설계서 §4): {success, data|error, timestamp, request_id}."""

import uuid
from datetime import datetime, timezone
from typing import Any

from flask import jsonify


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_id() -> str:
    return uuid.uuid4().hex[:8]  # 로그 추적용 8자리


def ok(data: Any, status: int = 200):
    body = {
        "success": True,
        "data": data,
        "timestamp": _now_iso(),
        "request_id": _request_id(),
    }
    return jsonify(body), status


def fail(code: str, message: str, status: int = 400):
    body = {
        "success": False,
        "error": {"code": code, "message": message},
        "timestamp": _now_iso(),
        "request_id": _request_id(),
    }
    return jsonify(body), status
