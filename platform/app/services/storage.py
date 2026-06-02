import boto3
from app.config import settings

s3 = boto3.client(
    service_name="s3",
    endpoint_url=settings.r2_endpoint,
    aws_access_key_id=settings.r2_access_key_id,
    aws_secret_access_key=settings.r2_secret_access_key,
    region_name="auto",
)

def upload_csi(event_id: str, csi_bytes: bytes) -> str:
    key = f"events/{event_id}/csi.bin"
    s3.put_object(Bucket=settings.r2_bucket, Key=key, Body=csi_bytes)
    return key

def get_csi(event_id: str) -> bytes:
    key = f"events/{event_id}/csi.bin"
    obj = s3.get_object(Bucket=settings.r2_bucket, Key=key)
    return obj["Body"].read()

def delete_csi(event_id: str):
    key = f"events/{event_id}/csi.bin"
    s3.delete_object(Bucket=settings.r2_bucket, Key=key)
