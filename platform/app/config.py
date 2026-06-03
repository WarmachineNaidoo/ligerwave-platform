from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    supabase_jwt_secret: str
    secret_key: str = "change-this-in-production"
    environment: str = "development"
    app_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:8000"

    stripe_secret_key: str | None = None
    yoco_secret_key: str | None = None
    whatsapp_api_key: str | None = None
    whatsapp_phone_number_id: str | None = None
    admin_email: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str = "csi-raw"
    r2_endpoint: str | None = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
