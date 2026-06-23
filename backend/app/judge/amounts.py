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
    못 찾으면 rider.unit_amount 로 폴백한다.
    """
    ca = case.get("coverage_amounts")
    rid = str(rider.get("id")) if rider.get("id") is not None else None
    rname = rider.get("name")

    if isinstance(ca, dict) and ca:
        for key in (rid, rname):
            if key is not None and key in ca:
                v = ca[key]
                return v.get("amount") if isinstance(v, dict) else v
        
        # 이름 부분 일치 매칭 (공백 및 '특별약관', '보장' 등 제거 비교)
        if rname:
            rname_clean = rname.replace(" ", "").replace("특별약관", "").replace("보장", "")
            for k, v in ca.items():
                if not k:
                    continue
                k_clean = str(k).replace(" ", "").replace("특별약관", "").replace("보장", "")
                if k_clean in rname_clean or rname_clean in k_clean:
                    return v.get("amount") if isinstance(v, dict) else v
        return None

    elif isinstance(ca, list) and ca:
        for item in ca:
            if not isinstance(item, dict):
                continue
            if item.get("rider_id") is not None and str(item.get("rider_id")) == rid:
                return item.get("amount")
            
            # 리스트 아이템의 name 부분 일치 매칭
            item_name = item.get("rider_name") or item.get("coverage_key")
            if item_name and rname:
                item_name_clean = str(item_name).replace(" ", "").replace("특별약관", "").replace("보장", "")
                rname_clean = rname.replace(" ", "").replace("특별약관", "").replace("보장", "")
                if item_name_clean in rname_clean or rname_clean in item_name_clean:
                    return item.get("amount")
        return None

    return rider.get("unit_amount")


def resolve_covered(case: Case, rider: Rider) -> int | None:
    """실손 covered_amount(보상대상 의료비)를 특약별로 찾는다.

    같은 결제건이라도 급여/비급여 특약마다 보상대상 금액이 다르므로 특약별로 받는다.
    못 찾으면 case.payment_amount(총 결제금액)로 폴백한다.
    """
    cov = case.get("covered_amounts") or case.get("coverage_amounts")
    rid = str(rider.get("id")) if rider.get("id") is not None else None
    rname = rider.get("name")
    
    if isinstance(cov, dict):
        for key in (rid, rname):
            if key is not None and key in cov:
                v = cov[key]
                return v.get("amount") if isinstance(v, dict) else v
                
        if rname:
            rname_clean = rname.replace(" ", "").replace("특별약관", "").replace("보장", "")
            for k, v in cov.items():
                if not k:
                    continue
                k_clean = str(k).replace(" ", "").replace("특별약관", "").replace("보장", "")
                if k_clean in rname_clean or rname_clean in k_clean:
                    return v.get("amount") if isinstance(v, dict) else v
                    
    elif isinstance(cov, list):
        for item in cov:
            if not isinstance(item, dict):
                continue
            if item.get("rider_id") is not None and str(item.get("rider_id")) == rid:
                return item.get("amount")
                
            item_name = item.get("rider_name") or item.get("coverage_key")
            if item_name and rname:
                item_name_clean = str(item_name).replace(" ", "").replace("특별약관", "").replace("보장", "")
                rname_clean = rname.replace(" ", "").replace("특별약관", "").replace("보장", "")
                if item_name_clean in rname_clean or rname_clean in item_name_clean:
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
