from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_base_url(value: str) -> str:
    cleaned = value.strip().rstrip(",").strip()
    return cleaned.rstrip("/")


class SystemOneSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JEV_", extra="ignore")

    base_url: str
    api_key: str
    model: str | None = None

    @field_validator("base_url", mode="before")
    @classmethod
    def _normalize_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPENAI_", extra="ignore")

    base_url: str
    api_key: str
    model: str

    @field_validator("base_url", mode="before")
    @classmethod
    def _normalize_base_url(cls, v: str) -> str:
        return _normalize_base_url(v)


class UnicornSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="UNICORN_", extra="ignore")

    host: str
    port: int


class MongoDBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MONGO_", extra="ignore")

    uri: str
    database: str


class GnaniSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GNANI_", extra="ignore")

    api_key: str


class AllowedOriginsSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CORS_", extra="ignore")

    allowed_origins: list[str]


systemone_settings = SystemOneSettings()
openai_settings = OpenAISettings()
mongodb_settings = MongoDBSettings()
gnani_settings = GnaniSettings()
cors_settings = AllowedOriginsSettings()
unicorn_settings = UnicornSettings()