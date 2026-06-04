from datetime import datetime, timezone, timedelta
from app.database import service
from app.services.storage import delete_csi

AUDIT_RETENTION_YEARS = 3

def purge_old_events():
    now = datetime.now(timezone.utc)
    homes = service.table("homes").select("id,retention_days").execute()
    for home in homes.data or []:
        cutoff = now - timedelta(days=home["retention_days"])
        old = service.table("events").select("id").lt("timestamp", cutoff.isoformat()).eq("home_id", home["id"]).execute()
        for event in old.data or []:
            csi = service.table("csi_raw").select("storage_path").eq("event_id", event["id"]).execute()
            for c in csi.data or []:
                try: delete_csi(event["id"])
                except: pass
            service.table("csi_raw").delete().eq("event_id", event["id"]).execute()
            service.table("events").delete().eq("id", event["id"]).execute()

def purge_old_audit_logs():
    cutoff = datetime.now(timezone.utc) - timedelta(days=365 * AUDIT_RETENTION_YEARS)
    old = service.table("audit_logs").select("id,user_id").lt("timestamp", cutoff.isoformat()).limit(1000).execute()
    for log in old.data or []:
        service.table("audit_logs").update({
            "user_id": None,
            "details": '{"anonymized":true}'
        }).eq("id", log["id"]).execute()

def purge_all():
    purge_old_events()
    purge_old_audit_logs()
