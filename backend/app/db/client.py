import os
import threading

from supabase import create_client

from app.config import settings
from app.db.mock_db import MockSupabaseClient

# 스레드별 Supabase 클라이언트 관리를 위한 thread-local storage
_local = threading.local()


def get_client():
    if getattr(_local, "client", None) is not None:
        return _local.client

    if os.environ.get("MOCK_DB") == "True":
        print("[DB] Using MockSupabaseClient for database (forced by MOCK_DB=True).")
        _local.client = MockSupabaseClient()
        return _local.client

    if settings.supabase_url and settings.supabase_key:
        try:
            _local.client = create_client(settings.supabase_url, settings.supabase_key)
            print("[DB] Initialized real Supabase client for current thread.")
            return _local.client
        except Exception as e:
            print(f"[DB] Failed to initialize real Supabase client: {e}. Falling back to Mock DB.")

    print("[DB] Using MockSupabaseClient for database.")
    _local.client = MockSupabaseClient()
    return _local.client
