from datetime import datetime, timezone, timedelta
from app.database import supabase
from app.services.storage import delete_csi

def purge_old_events():
    now = datetime.now(timezone.utc)
    homes = supabase.table("homes").select("id,retention_days").execute()
    for home in homes.data or []:
        cutoff = now - timedelta(days=home["retention_days"])
        old = supabase.table("events").select("id").lt("timestamp", cutoff.isoformat()).eq("home_id", home["id"]).execute()
        for event in old.data or []:
            csi = supabase.table("csi_raw").select("storage_path").eq("event_id", event["id"]).execute()
            for c in csi.data or []:
                try: delete_csi(event["id"])
                except: pass
            supabase.table("csi_raw").delete().eq("event_id", event["id"]).execute()
            supabase.table("events").delete().eq("id", event["id"]).execute()
