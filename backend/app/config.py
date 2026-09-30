from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    storage_bucket: str = "assignment-submissions"
    frontend_url: str = "http://localhost:5173"
    max_upload_mb: int = 10
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
