from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str
    jwt_secret_key: str = "dev-secret-key-change-in-production"

    model_config = {"env_file": ".env"}


settings = Settings()