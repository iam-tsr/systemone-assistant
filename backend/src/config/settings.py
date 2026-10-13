from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SystemOneSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="JEV_", extra="ignore")

    base_url: str
    api_key: str | None = None
    model: str | None = None

    @field_validator("base_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class OpenAISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPENAI_", extra="ignore")

    base_url: str
    api_key: str
    model: str

    @field_validator("base_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


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