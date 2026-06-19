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
        self._initialized = False

    def initialize_if_needed(self):
        if self._initialized:
            return

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

        self._initialized = True


db_instance = InMemoryDB()


class MockAPIResponse:
    def __init__(self, data):
        self.data = data


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

        if self._limit_count is not None:
            results = results[: self._limit_count]

        return MockAPIResponse(results)


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
        else:
            raise ValueError(f"Unknown table: {table_name}")
