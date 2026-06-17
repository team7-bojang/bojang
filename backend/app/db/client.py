from supabase import create_client
from app.config import settings
from app.db.mock_db import MockSupabaseClient

# Supabase 클라이언트 싱글턴 인스턴스
_client = None

def get_client():
    global _client
    if _client is not None:
        return _client

    if settings.supabase_url and settings.supabase_key:
        try:
            _client = create_client(settings.supabase_url, settings.supabase_key)
            print("[DB] Initialized real Supabase client.")
            return _client
        except Exception as e:
            print(f"[DB] Failed to initialize real Supabase client: {e}. Falling back to Mock DB.")
    
    print("[DB] Using MockSupabaseClient for database.")
    _client = MockSupabaseClient()
    return _client

