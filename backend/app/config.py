from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    HF_API_TOKEN: str
    HF_MODEL_ID: str = "mistralai/Mistral-7B-Instruct-v0.3"
    TURSO_DATABASE_URL: str = ""
    TURSO_AUTH_TOKEN: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    MY_EMAIL: str
    MY_SECRET: str
    REDIS_URL: str = "redis://localhost:6379"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"


settings = Settings()
