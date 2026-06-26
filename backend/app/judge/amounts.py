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
    단일 숫자로 전달된 경우 모든 특약에 동일하게 적용한다 (Case 2 비교 시나리오용).
    못 찾으면 rider.unit_amount 로 폴백한다.
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

    return rider.get("unit_amount")


def resolve_covered(case: Case, rider: Rider) -> int | None:
    """실손 covered_amount(보상대상 의료비)를 특약별로 찾는다.

    같은 결제건이라도 급여/비급여 특약마다 보상대상 금액이 다르므로 특약별로 받는다.
    못 찾으면 case.payment_amount(총 결제금액)로 폴백한다.
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
    return case.get("payment_amount")


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
