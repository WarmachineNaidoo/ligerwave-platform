import os
os.environ["SUPABASE_URL"] = os.environ.get("SUPABASE_URL") or "http://localhost:8000"
os.environ["SUPABASE_KEY"] = os.environ.get("SUPABASE_KEY") or "test-key"
os.environ["SUPABASE_SERVICE_KEY"] = os.environ.get("SUPABASE_SERVICE_KEY") or "test-service-key"
os.environ["SUPABASE_JWT_SECRET"] = os.environ.get("SUPABASE_JWT_SECRET") or "test-jwt-secret"

from unittest.mock import MagicMock, patch
_patcher = patch("supabase.create_client", return_value=MagicMock())
_patcher.start()