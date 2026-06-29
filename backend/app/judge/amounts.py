"""금액 산출 보조 — 가입금액 조회 · 실손 formula 안전 평가.

⚠️ 이중차감 금지: 실손은 claim_rule.formula 를 '그대로' 평가한다.
   비율·공제를 추가로 곱·차감하지 않는다 (formula 안에 이미 포함됨).
"""

from __future__ import annotations

import ast
import operator
from typing import Any

from app.judge.types import Case, Rider


def resolve_subscribed(case: Case, rider: Rider) -> int | None:
    """case.coverage_amounts 에서 이 특약의 '가입금액'을 찾는다.

    약관(riders)에는 가입금액이 없으므로 개인별 입력(coverage_amounts)에서 받는다.
    단일 숫자로 전달되면 모든 특약에 동일 적용한다 (Case 2 비교 시나리오용).
    못 찾으면 None(보류) — rider.unit_amount(시드 기본값 등 임의값)로 폴백하지 않는다.
    가입금액이 입력돼야만 정액 예상보험금을 산출한다.
    """
    ca = case.get("coverage_amounts")
    if isinstance(ca, (int, float)):
        return int(ca)
    rid = rider.get("id")
    rname = rider.get("name")

    if isinstance(ca, dict):
        keys = []
        if rid is not None:
            keys.append(rid)
            keys.append(str(rid))
        if rname is not None:
            keys.append(rname)
        for key in keys:
            if key in ca:
                v = ca[key]
                return v.get("amount") if isinstance(v, dict) else v
    elif isinstance(ca, list):
        for item in ca:
            if not isinstance(item, dict):
                continue
            item_rid = item.get("rider_id")
            if rid is not None and item_rid is not None:
                if str(item_rid) == str(rid):
                    return item.get("amount")
            if item.get("rider_name") == rname or item.get("coverage_key") == rname:
                return item.get("amount")

    return None


def resolve_covered(case: Case, rider: Rider) -> int | None:
    """실손 covered_amount(보상대상 의료비)를 특약별로 찾는다.

    우선순위:
      1) per-rider covered_amounts (특약별 직접 지정, 가장 구체적)
      2) 급여/비급여 버킷 — claim_rule.medical_category 로 분기
         · "비급여"(비급여·3대비급여) → case.non_covered_amount (비급여 의료비)
         · "급여"                      → case.patient_paid_amount (급여 본인부담금)
    못 찾으면 None(보류) — payment_amount(급여본인부담+전액본인+비급여 합계)는
    버킷이 섞여 과대산정되므로 실손 covered 로 쓰지 않는다.
    """
    cov = case.get("covered_amounts")
    rid = rider.get("id")
    rname = rider.get("name")
    if isinstance(cov, dict):
        keys = []
        if rid is not None:
            keys.append(rid)
            keys.append(str(rid))
        if rname is not None:
            keys.append(rname)
        for key in keys:
            if key in cov:
                v = cov[key]
                return v.get("amount") if isinstance(v, dict) else v
    elif isinstance(cov, list):
        for item in cov:
            if not isinstance(item, dict):
                continue
            item_rid = item.get("rider_id")
            if rid is not None and item_rid is not None:
                if str(item_rid) == str(rid):
                    return item.get("amount")
            if item.get("rider_name") == rname or item.get("coverage_key") == rname:
                return item.get("amount")

    # 급여/비급여 버킷 라우팅 — "비급여"가 "급여"의 상위 문자열이므로 비급여를 먼저 본다.
    medical_category = (rider.get("claim_rule") or {}).get("medical_category") or ""
    if "비급여" in medical_category:
        return case.get("non_covered_amount")
    if "급여" in medical_category:
        return case.get("patient_paid_amount")
    return None


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}
_ALLOWED_FUNCS = {"min": min, "max": max}


def _eval_node(node: ast.AST, names: dict[str, Any]) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        return names[node.id]  # 미지 변수 → KeyError → 보류
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left, names), _eval_node(node.right, names))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand, names)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        fn = _ALLOWED_FUNCS[node.func.id]  # 미허용 함수 → KeyError → 보류
        return fn(*(_eval_node(a, names) for a in node.args))
    raise ValueError("unsupported expression")


def eval_formula(formula: str | None, covered_amount: int | None) -> int | None:
    """실손 formula 를 그대로 평가한다.

    covered_amount(= 결제금액/본인부담금)만 알려진 변수로 둔다.
    by_table·상급병실료 등 미지 변수가 들어간 formula 는 None(보류)을 반환한다.
    """
    if not formula or covered_amount is None:
        return None
    try:
        tree = ast.parse(formula, mode="eval")
        return int(_eval_node(tree.body, {"covered_amount": covered_amount}))
    except Exception:
        return None
