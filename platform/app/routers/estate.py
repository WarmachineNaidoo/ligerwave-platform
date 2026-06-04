from fastapi import APIRouter, HTTPException, Depends
from app.middleware.auth import get_current_user
from app.database import service
from app.services.estate import estates, EstatePerimeter

router = APIRouter(prefix="/estate", tags=["estate"])

@router.get("/perimeter/{estate_id}")
async def get_perimeter(estate_id: str, payload: dict = Depends(get_current_user)):
    if estate_id not in estates:
        estates[estate_id] = EstatePerimeter(estate_id)
    return estates[estate_id].get_perimeter_summary()

@router.get("/heatmap/{estate_id}")
async def get_estate_heatmap(estate_id: str, payload: dict = Depends(get_current_user)):
    homes = service.table("homes").select("id,name,lat,lng").eq("organization_id", estate_id).execute()
    zone_data = []
    for home in homes.data or []:
        events = service.table("events").select("confidence,zone,timestamp").eq("home_id", home["id"]).gte("timestamp", "now() - interval '24 hours'").order("timestamp", desc=True).execute()
        zone_data.append({"home": home, "events": events.data or []})
    return {"estate_id": estate_id, "zones": zone_data}

@router.post("/zones/{estate_id}")
async def configure_zone(estate_id: str, body: dict, payload: dict = Depends(get_current_user)):
    if estate_id not in estates:
        estates[estate_id] = EstatePerimeter(estate_id)
    estates[estate_id].add_zone(body.get("zone_id"), body.get("zone_type", "perimeter"), body.get("sensitivity", 0.8))
    return {"status": "zone_added", "estate_id": estate_id, "zone_id": body.get("zone_id")}
