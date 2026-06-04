import boto3
from botocore.config import Config
s3 = boto3.client(
    service_name='s3',
    endpoint_url='https://d54e45b7f5d2506425a2f71df4d7e1e6.r2.cloudflarestorage.com',
    aws_access_key_id='d8f9afe9376f4932148f9f82a24b8e1c',
    aws_secret_access_key='2384a23e68c792050bc09cc9e83d431c259f86b6d0f52e05b31ec92c3bab5ea8',
    region_name='auto',
    config=Config(s3={'addressing_style': 'path'}),
)
try:
    s3.head_bucket(Bucket='csi-raw')
    print('Bucket csi-raw exists and is accessible')
    s3.put_object(Bucket='csi-raw', Key='test/connection_check.txt', Body=b'ok')
    print('Write OK')
    obj = s3.get_object(Bucket='csi-raw', Key='test/connection_check.txt')
    print(f'Read OK: {obj["Body"].read().decode()}')
    s3.delete_object(Bucket='csi-raw', Key='test/connection_check.txt')
    print('Delete OK')
    print('R2 fully configured and working')
except Exception as e:
    error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
    print(f'R2 error ({error_code}): {e}')
