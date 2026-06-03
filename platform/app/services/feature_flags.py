import httpx, json
from typing import Dict, List, Optional
from app.config import settings as app_settings

STAGES = ["dev", "alpha", "beta", "ga"]

DEFAULT_CONFIG = {
    "door_window": {"stage": "dev", "testers": []},
    "vehicle": {"stage": "dev", "testers": []},
    "fire_smoke": {"stage": "dev", "testers": []},
    "heart_rate": {"stage": "dev", "testers": []},
    "gait_id": {"stage": "dev", "testers": []},
    "routine_dev": {"stage": "dev", "testers": []},
    "baby_cry": {"stage": "dev", "testers": []},
    "room_occupancy": {"stage": "dev", "testers": []},
    "smart_triggers": {"stage": "dev", "testers": []},
    "water_leak": {"stage": "dev", "testers": []},
    "structural": {"stage": "dev", "testers": []},
}

SUPABASE_URL = app_settings.supabase_url
SERVICE_KEY = app_settings.supabase_service_key

def _headers():
    # WARNING: Uses service_role key — keep this server-side only, never expose to clients
    return {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}

def _get_admin_id() -> Optional[str]:
    """Find admin user by role or configured email."""
    email = app_settings.admin_email
    if email:
        r = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users", params={"email": email}, headers=_headers(), timeout=10)
        if r.status_code == 200:
            users = r.json().get("users", [])
            if users:
                return users[0]["id"]
    # Fallback: first user with role=admin in user_metadata
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users", headers=_headers(), timeout=10)
    if r.status_code == 200:
        for u in r.json().get("users", []):
            meta = u.get("user_metadata", {}) or {}
            if meta.get("role") == "admin":
                return u["id"]
    return None

def _get_admin_meta() -> dict:
    """Fetch admin user metadata via GoTrue admin API."""
    admin_id = _get_admin_id()
    if not admin_id:
        return {}
    r = httpx.get(f"{SUPABASE_URL}/auth/v1/admin/users/{admin_id}", headers=_headers(), timeout=10)
    if r.status_code != 200:
        return {}
    return r.json().get("user_metadata", {}) or {}

def _update_admin_meta(meta: dict):
    """Update admin user metadata via GoTrue admin API."""
    admin_id = _get_admin_id()
    if not admin_id:
        return
    httpx.put(f"{SUPABASE_URL}/auth/v1/admin/users/{admin_id}", headers=_headers(), json={"user_metadata": meta}, timeout=10)

def _load_config() -> Dict:
    meta = _get_admin_meta()
    return meta.get("feature_flags", dict(DEFAULT_CONFIG))

def _save_config(config: Dict):
    meta = _get_admin_meta()
    meta["feature_flags"] = config
    _update_admin_meta(meta)

def get_all_features() -> Dict:
    return _load_config()

def get_feature(feature_key: str) -> Optional[Dict]:
    return _load_config().get(feature_key)

def set_stage(feature_key: str, stage: str) -> Dict:
    if stage not in STAGES:
        return {"error": f"invalid_stage: must be one of {STAGES}"}
    config = _load_config()
    if feature_key not in config:
        config[feature_key] = {"stage": "dev", "testers": []}
    config[feature_key]["stage"] = stage
    _save_config(config)
    return {"feature": feature_key, "stage": stage}

def add_tester(feature_key: str, user_id: str) -> Dict:
    config = _load_config()
    if feature_key not in config:
        config[feature_key] = {"stage": "dev", "testers": []}
    if user_id not in config[feature_key]["testers"]:
        config[feature_key]["testers"].append(user_id)
    _save_config(config)
    return {"feature": feature_key, "testers": config[feature_key]["testers"]}

def remove_tester(feature_key: str, user_id: str) -> Dict:
    config = _load_config()
    if feature_key in config:
        config[feature_key]["testers"] = [t for t in config[feature_key]["testers"] if t != user_id]
    _save_config(config)
    return {"feature": feature_key, "testers": config[feature_key].get("testers", [])}

def is_available(feature_key: str, user_id: str) -> bool:
    config = _load_config()
    feature = config.get(feature_key, {})
    stage = feature.get("stage", "dev")
    admin_id = _get_admin_id()

    if stage == "ga":
        return True
    if stage == "beta":
        return True
    if admin_id and user_id == admin_id:
        return True
    if stage in ("alpha", "dev") and user_id in feature.get("testers", []):
        return True
    return False

def get_available_features(user_id: str) -> List[str]:
    return [k for k in _load_config() if is_available(k, user_id)]
