from typing import Dict, List, Optional
from app.database import service

# Feature definitions with their tier and monthly price
FEATURES = {
    "door_window":     {"tier": "security",   "price": 30,  "label": "Door/Window Detection",       "desc": "Detect open/close events without contact sensors"},
    "vehicle":         {"tier": "security",   "price": 30,  "label": "Vehicle Detection",            "desc": "Know when a car arrives or leaves the driveway"},
    "fire_smoke":      {"tier": "security",   "price": 30,  "label": "Fire/Smoke Proxy",             "desc": "Detect fire signature via CSI air turbulence"},
    "heart_rate":      {"tier": "wellness",   "price": 30,  "label": "Heart Rate Monitoring",        "desc": "Extract heart rate from CSI phase signal"},
    "gait_id":         {"tier": "intel",      "price": 30,  "label": "Gait Identification",          "desc": "Identify who is in the house by walking pattern"},
    "routine_dev":     {"tier": "intel",      "price": 30,  "label": "Routine Deviation",            "desc": "Alert on unusual activity vs learned schedule"},
    "baby_cry":        {"tier": "intel",      "price": 30,  "label": "Baby Cry Detection",           "desc": "Detect crying via CSI vibration pattern"},
    "room_occupancy":  {"tier": "intel",      "price": 30,  "label": "Room Occupancy Heatmap",       "desc": "How many people in each room over time"},
    "smart_triggers":  {"tier": "intel",      "price": 30,  "label": "Smart Home Triggers",          "desc": "Automate lights, geyser, alarm on occupancy"},
    "water_leak":      {"tier": "intel",      "price": 30,  "label": "Water Leak Detection",         "desc": "Detect water leaks via CSI dielectric change"},
    "structural":      {"tier": "intel",      "price": 30,  "label": "Structural Movement Monitor",  "desc": "Detect subtle foundation shifts over time"},
}

TIERS = {
    "free":       {"label": "Free",          "monthly": 0,   "features": [],                              "ws_priority": 0},
    "security":   {"label": "Security+",     "monthly": 30,  "features": ["door_window", "vehicle", "fire_smoke"], "ws_priority": 1},
    "wellness":   {"label": "Wellness+",     "monthly": 30,  "features": ["heart_rate"],                  "ws_priority": 1},
    "intel":      {"label": "Intelligence+", "monthly": 30,  "features": ["gait_id", "routine_dev", "baby_cry", "room_occupancy", "smart_triggers", "water_leak", "structural"], "ws_priority": 1},
    "premium":    {"label": "Premium Bundle", "monthly": 80,  "features": ["door_window", "vehicle", "fire_smoke", "heart_rate", "gait_id", "routine_dev", "baby_cry", "room_occupancy", "smart_triggers", "water_leak", "structural"], "ws_priority": 1},
    "ar_premium": {"label": "AR Premium",     "monthly": 100, "features": ["door_window", "vehicle", "fire_smoke", "heart_rate", "gait_id", "routine_dev", "baby_cry", "room_occupancy", "smart_triggers", "water_leak", "structural"], "ws_priority": 3},
}

def get_ws_priority(home_id: str) -> int:
    """Get WebSocket push priority for a home (higher = faster)."""
    home = service.table("homes").select("tier").eq("id", home_id).execute()
    if not home.data:
        return 0
    tier = home.data[0].get("tier", "free")
    return TIERS.get(tier, TIERS["free"]).get("ws_priority", 0)

def get_subscribed_features(home_id: str) -> List[str]:
    """Get the list of enabled feature keys for a home."""
    home = service.table("homes").select("tier,enabled_features").eq("id", home_id).execute()
    if not home.data:
        return []
    row = home.data[0]
    tier = row.get("tier", "free")
    enabled = set(row.get("enabled_features") or [])
    # Base features from tier
    base = list(TIERS.get(tier, TIERS["free"])["features"])
    # Merge individually enabled features
    for f in enabled:
        if f not in base:
            base.append(f)
    return base

def has_feature(home_id: str, feature_key: str) -> bool:
    """Check if a home has access to a specific feature."""
    return feature_key in get_subscribed_features(home_id)

def set_tier(home_id: str, tier: str) -> dict:
    """Upgrade or downgrade a home's subscription tier."""
    if tier not in TIERS:
        return {"error": "invalid_tier"}
    service.table("homes").update({"tier": tier}).eq("id", home_id).execute()
    return {"tier": tier, "features": TIERS[tier]["features"], "price": TIERS[tier]["monthly"]}

def toggle_feature(home_id: str, feature_key: str, enable: bool) -> dict:
    """Enable or disable an individual feature for a home."""
    if feature_key not in FEATURES:
        return {"error": "invalid_feature"}
    home = service.table("homes").select("enabled_features").eq("id", home_id).execute()
    current = set(home.data[0].get("enabled_features") or []) if home.data else set()
    if enable:
        current.add(feature_key)
    else:
        current.discard(feature_key)
    service.table("homes").update({"enabled_features": list(current)}).eq("id", home_id).execute()
    return {"feature": feature_key, "enabled": enable}
