import json
import uuid
from datetime import UTC, datetime
from pathlib import Path


# Mock DB 데이터 홀더
class InMemoryDB:
    def __init__(self):
        self.policies = []
        self.riders = []
        self.rider_chunks = []
        self.cases = []
        self.analysis_results = []
        self.reports = []
        self.diseases = []
        self.treatment_types = []
        self.disease_group_aliases = []
        self.disease_group_code_rules = []
        self.disease_groups = []
        self.rider_treatment_rules = []
        self._initialized = False

    def initialize_if_needed(self):
        if self._initialized:
            return

        # disease_groups 사전 모의 생성
        self.disease_groups.extend([
            {"id": "stroke", "name": "뇌혈관질환", "user_label": "뇌졸중/뇌경색"},
            {"id": "cancer", "name": "암", "user_label": "암/악성신생물"},
            {"id": "disc_disease", "name": "추간판장애", "user_label": "허리디스크/목디스크"},
            {"id": "fracture", "name": "골절", "user_label": "골절/뼈부러짐"},
        ])

        # disease_group_aliases 및 rules 사전 모의 생성
        self.disease_group_aliases.extend([
            {"id": 1, "group_id": "disc_disease", "alias": "허리디스크", "source": "service"},
            {"id": 2, "group_id": "disc_disease", "alias": "목디스크", "source": "service"},
            {"id": 3, "group_id": "disc_disease", "alias": "디스크", "source": "service"},
            {"id": 4, "group_id": "fracture", "alias": "골절", "source": "service"},
            {"id": 5, "group_id": "stroke", "alias": "뇌경색", "source": "service"},
            {"id": 6, "group_id": "stroke", "alias": "뇌졸중", "source": "service"},
            {"id": 7, "group_id": "cancer", "alias": "암", "source": "service"},
            {"id": 8, "group_id": "cancer", "alias": "위암", "source": "service"},
        ])
        
        self.disease_group_code_rules.extend([
            {'id': 1, 'group_id': 'stroke', 'rule_type': 'include', 'code_start': 'I60', 'code_end': 'I69', 'code_system': 'KCD', 'confidence': 'high', 'note': '뇌혈관질환'},
            {'id': 2, 'group_id': 'cancer', 'rule_type': 'include', 'code_start': 'C00', 'code_end': 'D09', 'code_system': 'KCD', 'confidence': 'high', 'note': '악성신생물'},
            {'id': 3, 'group_id': 'disc_disease', 'rule_type': 'include', 'code_start': 'M50', 'code_end': 'M51', 'code_system': 'KCD', 'confidence': 'medium', 'note': '디스크'},
            {'id': 4, 'group_id': 'fracture', 'rule_type': 'include', 'code_start': 'S02', 'code_end': 'S92', 'code_system': 'KCD', 'confidence': 'policy_review_required', 'note': '골절'},
        ])

        # treatment_types 사전 생성
        preset_treatments = [
            {"code": "MRI_MRA", "name": "MRI / MRA 검사"},
            {"code": "XRAY", "name": "엑스레이"},
            {"code": "INJECTION", "name": "주사치료"},
            {"code": "MANUAL_THERAPY", "name": "도수치료"},
            {"code": "PHYSICAL_THERAPY", "name": "물리치료"},
            {"code": "ETC", "name": "기타"},
        ]
        self.treatment_types.extend(preset_treatments)

        # 0. 질병 정보 사전 생성
        preset_diseases = [
            {"kcd": "I63", "name": "뇌경색증", "search_text": "뇌경색증 뇌혈관 I63"},
            {"kcd": "I60", "name": "지주막하출혈", "search_text": "지주막하출혈 뇌출혈 I60"},
            {"kcd": "I61", "name": "뇌내출혈", "search_text": "뇌내출혈 뇌출혈 I61"},
            {
                "kcd": "C16",
                "name": "위의 악성 신생물 (위암)",
                "search_text": "위의 악성 신생물 (위암) C16 위암",
            },
            {"kcd": "C34", "name": "폐암", "search_text": "폐암 C34"},
            {
                "kcd": "M51",
                "name": "기타 추간판 장애 (허리디스크)",
                "search_text": "기타 추간판 장애 (허리디스크) 디스크 M51",
            },
            {"kcd": "J30", "name": "혈관운동성 및 알레르기성 비염", "search_text": "비염 J30"},
            {"kcd": "E11", "name": "2형 당뇨병", "search_text": "당뇨병 E11"},
            {"kcd": "I21", "name": "급성 심근경색증", "search_text": "급성 심근경색증 심장 I21"},
            {
                "kcd": "S62",
                "name": "손목 및 손부위의 골절",
                "search_text": "손목 및 손부위의 골절 골절 S62 손목",
            },
            {
                "kcd": "S63",
                "name": "손목 및 손부위의 관절 및 인대의 탈구, 염좌 및 긴장",
                "search_text": ("손목 및 손부위의 관절 및 인대의 탈구, 염좌 및 긴장 염좌 S63 손목"),
            },
            {
                "kcd": "S60",
                "name": "손목 및 손의 표재성 손상 (손목 타박상)",
                "search_text": "손목 및 손의 표재성 손상 타박상 S60 손목",
            },
            {
                "kcd": "S635",
                "name": "손목 인대 손상",
                "search_text": "손목 인대 손상 인대 S635 손목",
            },
        ]
        self.diseases.extend(preset_diseases)

        # 1. Preset 보험 상품 생성
        preset_policies = [
            {
                "id": "p-db-3dae",
                "name": "DB 3대질병",
                "insurer": "DB손해보험",
                "type": "질병",
                "is_preset": True,
                "pdf_path": None,
            },
            {
                "id": "p-hd-silsil",
                "name": "현대 실손",
                "insurer": "현대해상",
                "type": "실손",
                "is_preset": True,
                "pdf_path": None,
            },
            {
                "id": "p-hw-cancer",
                "name": "한화 e암보험",
                "insurer": "한화생명",
                "type": "암",
                "is_preset": True,
                "pdf_path": None,
            },
            {
                "id": "p-mr-sanghae",
                "name": "메리츠 상해안심",
                "insurer": "메리츠화재",
                "type": "상해",
                "is_preset": True,
                "pdf_path": None,
            },
        ]
        self.policies.extend(preset_policies)

        # 2. 보험약관데이터.json 로드하여 특약(riders) 적재
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "보험약관데이터.json"
        if data_path.exists():
            try:
                with open(data_path, encoding="utf-8") as f:
                    raw_data = json.load(f)

                raw_riders = raw_data.get("riders", [])
                for _idx, r in enumerate(raw_riders):
                    rider_id = str(uuid.uuid4())

                    # 특약 명칭에 따른 보험 상품 매핑
                    name = r.get("name", "")

                    # 골든셋 및 데모 요구사항에 맞게 특약명 정규화
                    if "질병급여실손의료비" in name and "입원" in name:
                        name = "질병급여실손의료비(입원)"
                    elif "뇌혈관질환입원일당" in name:
                        name = "뇌혈관질환입원일당(4일이상120일한도)"
                    elif "질병입원일당" in name:
                        name = "질병입원일당(1일이상180일한도)"

                    if "실손" in name or r.get("claim_rule") is not None:
                        policy_id = "p-hd-silsil"
                    elif "암" in name:
                        policy_id = "p-hw-cancer"
                    elif "상해" in name or "골절" in name:
                        policy_id = "p-mr-sanghae"
                    else:
                        policy_id = "p-db-3dae"

                    source = r.get("source") or {}

                    rider_data = {
                        "id": rider_id,
                        "policy_id": policy_id,
                        "name": name,
                        "is_main": r.get("is_main", False),
                        "trigger_type": r.get("trigger_type"),
                        "trigger_detail": r.get("trigger_detail"),
                        "unit_amount": r.get("unit_amount"),
                        "unit_type": r.get("unit_type"),
                        "unit_basis": r.get("unit_basis"),
                        "boundaries": r.get("boundaries", []),
                        "exclusions": r.get("exclusions", []),
                        "limits": r.get("limits", []),
                        "waiting_period_days": r.get("waiting_period_days"),
                        "reductions": r.get("reductions", []),
                        "deduct_days": r.get("deduct_days", 0),
                        "claim_rule": r.get("claim_rule"),
                        "source_pages": r.get("source_pages", []),
                        "article_no": source.get("article"),
                        "page": source.get("page"),
                        "raw_text": source.get("raw_text"),
                        "verified": r.get("verified", True),
                    }
                    self.riders.append(rider_data)

                    # RAG 검색용 청크 미리 생성
                    content = f"특약명: {name}\n보장개요: {r.get('trigger_detail') or ''}\n지급기준: {r.get('unit_basis') or ''}\n제외사항: {' '.join(r.get('exclusions', []))}"
                    chunk_data = {
                        "id": str(uuid.uuid4()),
                        "rider_id": rider_id,
                        "content": content,
                        "embedding": None,
                        "meta": {
                            "policy_id": policy_id,
                            "page": source.get("page"),
                            "article_no": source.get("article"),
                            "trigger_type": r.get("trigger_type"),
                        },
                    }
                    self.rider_chunks.append(chunk_data)
            except Exception as e:
                print(f"[MockDB] Failed to load 보험약관데이터.json: {e}")
        else:
            print(f"[MockDB] 보험약관데이터.json not found at {data_path}")
            # 보험약관데이터.json 없을 때 골든셋 평가에 필요한 최소 특약 데이터 하드코딩
            self._load_golden_preset_riders()

        self._initialized = True

    def _load_golden_preset_riders(self):
        """골든셋 평가용 최소 특약 데이터를 Mock DB에 직접 적재."""
        golden_riders = [
            # ── DB 3대질병 (p-db-3dae) ──────────────────────────────────────────
            {
                "id": "r-db-hosp-daily",
                "policy_id": "p-db-3dae",
                "name": "질병입원일당(1일이상180일한도)",
                "trigger_type": "입원",
                "is_main": False,
                "verified": True,
                "unit_amount": 10000,
                "unit_type": "1일당",
                "boundaries": [{"condition_days": 1, "effect": "1일 이상 입원 시 첫날부터 지급"}],
                "deduct_days": 0,
                "limits": [{"scope": "per_hospitalization", "unit": "days", "value": 180}],
                "waiting_period_days": 0,
                "reductions": [],
                "exclusions": [],
                "claim_rule": None,
                "article_no": "제12조",
                "page": 45,
                "raw_text": (
                    "피보험자가 질병으로 인하여 1일 이상 입원하여 치료를 받은 경우 "
                    "첫날부터 입원 1일당 가입금액을 지급합니다. (180일 한도)"
                ),
            },
            {
                "id": "r-db-stroke-daily",
                "policy_id": "p-db-3dae",
                "name": "뇌혈관질환입원일당(4일이상120일한도)",
                "trigger_type": "입원",
                "is_main": False,
                "verified": True,
                "unit_amount": 30000,
                "unit_type": "1일당",
                "boundaries": [{"condition_days": 4, "effect": "4일 이상 입원 시 첫날부터 지급"}],
                "deduct_days": 0,
                "limits": [{"scope": "per_hospitalization", "unit": "days", "value": 120}],
                "waiting_period_days": 0,
                "reductions": [],
                "exclusions": ["비뇌혈관성 질환"],
                "claim_rule": None,
                "article_no": "제13조",
                "page": 48,
                "raw_text": (
                    "피보험자가 뇌혈관질환(KCD I60~I69)으로 4일 이상 입원 시 "
                    "첫날부터 입원 1일당 뇌혈관질환입원일당을 지급합니다. (120일 한도)"
                ),
            },
            # ── 현대 실손 (p-hd-silsil) ─────────────────────────────────────────
            {
                "id": "r-hd-silsil-hosp",
                "policy_id": "p-hd-silsil",
                "name": "질병급여실손의료비(입원)",
                "trigger_type": "입원",
                "is_main": False,
                "verified": True,
                "unit_amount": 50000000,
                "unit_type": "일시금",
                "boundaries": [],
                "deduct_days": 0,
                "limits": [],
                "waiting_period_days": 0,
                "reductions": [],
                "exclusions": [],
                "claim_rule": {
                    "formula": "min(50000000, actual_cost * 0.8)",
                    "copay_ratio": 0.2,
                    "deductible": {"type": "fixed", "value": 0},
                },
                "article_no": "제3조",
                "page": 12,
                "raw_text": (
                    "피보험자가 질병으로 입원하여 치료받은 경우 국민건강보험법에서 정한 "
                    "요양급여 중 본인부담금의 80%를 보상합니다. (5천만원 한도)"
                ),
            },
            # ── 한화 e암보험 (p-hw-cancer) ───────────────────────────────────────
            {
                "id": "r-hw-cancer-diag",
                "policy_id": "p-hw-cancer",
                "name": "암진단비(유사암제외)(감액없음)",
                "trigger_type": "진단",
                "is_main": False,
                "verified": True,
                "unit_amount": 30000000,
                "unit_type": "일시금",
                "boundaries": [{"condition_days": 0, "effect": "암(유사암 제외) 진단 확정 시 지급"}],
                "deduct_days": 0,
                "limits": [],
                "waiting_period_days": 90,
                "reductions": [],
                "exclusions": ["유사암", "제자리암", "경계성종양"],
                "claim_rule": None,
                "article_no": "제8조",
                "page": 22,
                "raw_text": (
                    "피보험자가 암(유사암, 제자리암, 경계성종양 제외)으로 진단 확정 시 "
                    "암진단비를 지급합니다. 감액없이 가입금액 전액 지급. (90일 면책)"
                ),
            },
            {
                "id": "r-hw-cancer-surgery",
                "policy_id": "p-hw-cancer",
                "name": "암수술비(복강경하,흉강경하)(유사암포함, 연간1회한)",
                "trigger_type": "수술",
                "is_main": False,
                "verified": True,
                "unit_amount": 2000000,
                "unit_type": "일시금",
                "boundaries": [{"condition_days": 0, "effect": "암 수술 시 지급 (복강경/흉강경 포함)"}],
                "deduct_days": 0,
                "limits": [{"scope": "annual", "unit": "count", "value": 1}],
                "waiting_period_days": 90,
                "reductions": [{"elapsed_days": 730, "ratio": 0.5}],
                "exclusions": [],
                "claim_rule": None,
                "article_no": "제9조",
                "page": 25,
                "raw_text": (
                    "피보험자가 암 수술(복강경하·흉강경하 포함, 유사암 포함)을 받은 경우 "
                    "연간 1회 한하여 암수술비를 지급합니다. 가입 2년 미만인 경우 50% 감액."
                ),
            },
            # ── 메리츠 상해안심 (p-mr-sanghae) ──────────────────────────────────
            {
                "id": "r-mr-fracture-diag",
                "policy_id": "p-mr-sanghae",
                "name": "골절진단비Ⅱ",
                "trigger_type": "진단",
                "is_main": False,
                "verified": True,
                "unit_amount": 500000,
                "unit_type": "일시금",
                "boundaries": [{"condition_days": 0, "effect": "골절 진단 확정 시 지급"}],
                "deduct_days": 0,
                "limits": [],
                "waiting_period_days": 0,
                "reductions": [],
                "exclusions": ["치아 파절", "병적 골절"],
                "claim_rule": None,
                "article_no": "제20조",
                "page": 72,
                "raw_text": (
                    "피보험자가 상해로 인하여 골절 진단을 받은 경우 골절진단비Ⅱ를 지급합니다. "
                    "단, 치아 파절 및 병적 골절은 제외합니다."
                ),
            },
        ]

        for rider in golden_riders:
            rider_id = rider["id"]
            policy_id = rider["policy_id"]
            self.riders.append(rider)

            # RAG 검색용 청크 생성
            content = (
                f"특약명: {rider['name']}\n"
                f"보장개요: {rider.get('raw_text', '')}\n"
                f"지급기준: {rider.get('unit_type', '')} {rider.get('unit_amount', '')}\n"
                f"제외사항: {' '.join(rider.get('exclusions', []))}"
            )
            self.rider_chunks.append({
                "id": str(uuid.uuid4()),
                "rider_id": rider_id,
                "content": content,
                "embedding": None,
                "meta": {
                    "policy_id": policy_id,
                    "page": rider.get("page"),
                    "article_no": rider.get("article_no"),
                    "trigger_type": rider.get("trigger_type"),
                },
            })


db_instance = InMemoryDB()


class MockAPIResponse:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count if count is not None else (len(data) if isinstance(data, list) else 1)


class MockQueryBuilder:
    def __init__(self, table_name, data_list):
        self.table_name = table_name
        self.data_list = data_list
        self._filters = []
        self._order_by = None
        self._limit_count = None
        self._select_columns = "*"
        self._is_insert = False
        self._is_update = False
        self._mutation_data = None
        self._range_start = None
        self._range_end = None

    def range(self, start, end):
        self._range_start = start
        self._range_end = end
        return self

    def select(self, columns="*"):
        self._select_columns = columns
        return self

    def insert(self, data):
        self._is_insert = True
        self._mutation_data = data
        return self

    def update(self, data):
        self._is_update = True
        self._mutation_data = data
        return self

    def eq(self, column, value):
        self._filters.append(("eq", column, value))
        return self

    def in_(self, column, value):
        self._filters.append(("in", column, value))
        return self

    def neq(self, column, value):
        self._filters.append(("neq", column, value))
        return self

    def ilike(self, column, value):
        self._filters.append(("ilike", column, value))
        return self

    def filter(self, column, operator, value):
        self._filters.append((operator, column, value))
        return self

    def or_(self, filter_str):
        self._filters.append(("or", None, filter_str))
        return self

    def order(self, column, descending=False):
        self._order_by = (column, descending)
        return self

    def limit(self, count):
        self._limit_count = count
        return self

    def _get_nested_val(self, obj, path):
        if "->" in path:
            parts = path.split("->")
            val = obj
            for part in parts:
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    return None
            return val
        return obj.get(path)

    def execute(self):
        db_instance.initialize_if_needed()

        if self._is_insert:
            rows = (
                self._mutation_data
                if isinstance(self._mutation_data, list)
                else [self._mutation_data]
            )
            inserted_rows = []
            for row in rows:
                new_row = row.copy()
                if "id" not in new_row:
                    new_row["id"] = str(uuid.uuid4())
                if "created_at" not in new_row:
                    new_row["created_at"] = datetime.now(UTC).isoformat()
                self.data_list.append(new_row)
                inserted_rows.append(new_row)
            return MockAPIResponse(
                inserted_rows if isinstance(self._mutation_data, list) else inserted_rows[0]
            )

        if self._is_update:
            filtered_indices = []
            for idx, item in enumerate(self.data_list):
                match = True
                for op, col, val in self._filters:
                    item_val = self._get_nested_val(item, col)
                    if op == "eq" and item_val != val:
                        match = False
                    elif op == "neq" and item_val == val:
                        match = False
                    elif op == "in" and item_val not in (val or []):
                        match = False
                if match:
                    filtered_indices.append(idx)

            updated_rows = []
            for idx in filtered_indices:
                self.data_list[idx].update(self._mutation_data)
                updated_rows.append(self.data_list[idx])
            return MockAPIResponse(updated_rows)

        results = []
        for item in self.data_list:
            match = True
            for op, col, val in self._filters:
                item_val = self._get_nested_val(item, col)
                if op == "eq" and item_val != val:
                    match = False
                elif op == "neq" and item_val == val:
                    match = False
                elif op == "in" and item_val not in (val or []):
                    match = False
                elif op == "cs" and isinstance(item_val, list):
                    if val not in item_val:
                        match = False
                elif op == "ilike":
                    val_clean = str(val).replace("%", "").lower()
                    item_val_str = str(item_val or "").lower()
                    if val_clean not in item_val_str:
                        match = False
                elif op == "or":
                    or_match = False
                    for cond in val.split(","):
                        parts = cond.split(".")
                        if len(parts) == 3:
                            col_name, operator, match_val = parts
                            match_val_clean = match_val.replace("%", "").lower()
                            item_field_val = str(item.get(col_name) or "").lower()
                            if operator == "ilike" and match_val_clean in item_field_val:
                                or_match = True
                                break
                    if not or_match:
                        match = False
            if match:
                res_item = item.copy()

                if self.table_name == "rider_chunks" and (
                    "riders(*)" in self._select_columns or "riders" in self._select_columns
                ):
                    rider = next(
                        (r for r in db_instance.riders if r["id"] == item["rider_id"]), None
                    )
                    if rider:
                        res_item["riders"] = rider.copy()

                if self.table_name == "riders" and (
                    "policies(*)" in self._select_columns or "policies" in self._select_columns
                ):
                    policy = next(
                        (p for p in db_instance.policies if p["id"] == item["policy_id"]), None
                    )
                    if policy:
                        res_item["policies"] = policy.copy()

                results.append(res_item)

        if self._order_by:
            col, desc = self._order_by
            results.sort(key=lambda x: x.get(col) or "", reverse=desc)

        total_count = len(results)

        if self._range_start is not None and self._range_end is not None:
            results = results[self._range_start : self._range_end + 1]

        if self._limit_count is not None:
            results = results[: self._limit_count]

        return MockAPIResponse(results, count=total_count)


class MockSupabaseClient:
    def table(self, table_name):
        db_instance.initialize_if_needed()
        if table_name == "policies":
            return MockQueryBuilder(table_name, db_instance.policies)
        elif table_name == "riders":
            return MockQueryBuilder(table_name, db_instance.riders)
        elif table_name == "rider_chunks":
            return MockQueryBuilder(table_name, db_instance.rider_chunks)
        elif table_name == "cases":
            return MockQueryBuilder(table_name, db_instance.cases)
        elif table_name == "analysis_results":
            return MockQueryBuilder(table_name, db_instance.analysis_results)
        elif table_name == "reports":
            return MockQueryBuilder(table_name, db_instance.reports)
        elif table_name == "diseases":
            return MockQueryBuilder(table_name, db_instance.diseases)
        elif table_name == "treatment_types":
            return MockQueryBuilder(table_name, db_instance.treatment_types)
        elif table_name == "disease_group_aliases":
            return MockQueryBuilder(table_name, db_instance.disease_group_aliases)
        elif table_name == "disease_group_code_rules":
            return MockQueryBuilder(table_name, db_instance.disease_group_code_rules)
        elif table_name == "disease_groups":
            return MockQueryBuilder(table_name, db_instance.disease_groups)
        elif table_name == "rider_treatment_rules":
            return MockQueryBuilder(table_name, db_instance.rider_treatment_rules)
        else:
            raise ValueError(f"Unknown table: {table_name}")
