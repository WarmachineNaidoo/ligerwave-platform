from fastapi import APIRouter, HTTPException, Depends
from app.middleware.auth import get_current_user
from app.database import service
from app.services.estate import estates, EstatePerimeter

router = APIRouter(prefix="/estate", tags=["estate"])

def _verify_org_access(payload: dict, requested_org_id: str = None) -> str:
    user_id = payload.get("sub")
    user = service.table("users").select("organization_id").eq("id", user_id).execute()
    if not user.data or not user.data[0].get("organization_id"):
        raise HTTPException(status_code=403, detail="Access denied")
    org_id = user.data[0]["organization_id"]
    if requested_org_id and requested_org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return org_id

@router.get("/perimeter/{estate_id}")
async def get_perimeter(estate_id: str, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload, estate_id)
    nskey = f"{org_id}:{estate_id}"
    if nskey not in estates:
        estates[nskey] = EstatePerimeter(estate_id)
    return estates[nskey].get_perimeter_summary()

@router.get("/heatmap/{estate_id}")
async def get_estate_heatmap(estate_id: str, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload, estate_id)
    homes = service.table("homes").select("id,name,lat,lng").eq("organization_id", org_id).execute()
    zone_data = []
    for home in homes.data or []:
        events = service.table("events").select("confidence,zone,timestamp").eq("home_id", home["id"]).gte("timestamp", "now() - interval '24 hours'").order("timestamp", desc=True).execute()
        zone_data.append({"home": home, "events": events.data or []})
    return {"estate_id": estate_id, "zones": zone_data}

@router.post("/zones/{estate_id}")
async def configure_zone(estate_id: str, body: dict, payload: dict = Depends(get_current_user)):
    org_id = _verify_org_access(payload, estate_id)
    nskey = f"{org_id}:{estate_id}"
    if nskey not in estates:
        estates[nskey] = EstatePerimeter(estate_id)
    estates[nskey].add_zone(body.get("zone_id"), body.get("zone_type", "perimeter"), body.get("sensitivity", 0.8))
    return {"status": "zone_added", "estate_id": estate_id, "zone_id": body.get("zone_id")}
