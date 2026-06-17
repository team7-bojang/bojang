import json
import uuid
from datetime import datetime, timezone
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
        self._initialized = False

    def initialize_if_needed(self):
        if self._initialized:
            return
        
        # 1. Preset 보험 상품 생성
        preset_policies = [
            {"id": "p-db-3dae", "name": "DB 3대질병", "insurer": "DB손해보험", "type": "질병", "is_preset": True, "pdf_path": None},
            {"id": "p-hd-silsil", "name": "현대 실손", "insurer": "현대해상", "type": "실손", "is_preset": True, "pdf_path": None},
            {"id": "p-hw-cancer", "name": "한화 e암보험", "insurer": "한화생명", "type": "암", "is_preset": True, "pdf_path": None},
            {"id": "p-mr-sanghae", "name": "메리츠 상해안심", "insurer": "메리츠화재", "type": "상해", "is_preset": True, "pdf_path": None},
        ]
        self.policies.extend(preset_policies)

        # 2. 보험약관데이터.json 로드하여 특약(riders) 적재
        data_path = Path(__file__).resolve().parent.parent.parent.parent / "보험약관데이터.json"
        if data_path.exists():
            try:
                with open(data_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    
                raw_riders = raw_data.get("riders", [])
                for idx, r in enumerate(raw_riders):
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
                        "verified": r.get("verified", True)
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
                            "trigger_type": r.get("trigger_type")
                        }
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

    def filter(self, column, operator, value):
        self._filters.append((operator, column, value))
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
            rows = self._mutation_data if isinstance(self._mutation_data, list) else [self._mutation_data]
            inserted_rows = []
            for row in rows:
                new_row = row.copy()
                if "id" not in new_row:
                    new_row["id"] = str(uuid.uuid4())
                if "created_at" not in new_row:
                    new_row["created_at"] = datetime.now(timezone.utc).isoformat()
                self.data_list.append(new_row)
                inserted_rows.append(new_row)
            return MockAPIResponse(inserted_rows if isinstance(self._mutation_data, list) else inserted_rows[0])

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
            if match:
                res_item = item.copy()
                
                if self.table_name == "rider_chunks" and ("riders(*)" in self._select_columns or "riders" in self._select_columns):
                    rider = next((r for r in db_instance.riders if r["id"] == item["rider_id"]), None)
                    if rider:
                        res_item["riders"] = rider.copy()
                
                if self.table_name == "riders" and ("policies(*)" in self._select_columns or "policies" in self._select_columns):
                    policy = next((p for p in db_instance.policies if p["id"] == item["policy_id"]), None)
                    if policy:
                        res_item["policies"] = policy.copy()

                results.append(res_item)

        if self._order_by:
            col, desc = self._order_by
            results.sort(key=lambda x: x.get(col) or "", reverse=desc)

        if self._limit_count is not None:
            results = results[:self._limit_count]

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
        else:
            raise ValueError(f"Unknown table: {table_name}")
