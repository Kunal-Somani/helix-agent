from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    ANTHROPIC_API_KEY: str
    MY_EMAIL: str
    MY_SECRET: str
    REDIS_URL: str = "redis://localhost:6379"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"


settings = Settings()
