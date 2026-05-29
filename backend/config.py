from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    google_application_credentials: str = ""
    firebase_project_id: str = ""
    cors_origins: str = "http://localhost:3000"
    mock_data_dir: str = str(Path(__file__).resolve().parent.parent / "mock_data")
    use_mock_db: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
