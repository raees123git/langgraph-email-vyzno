from pydantic import Field, HttpUrl, SecretStr, UUID4
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    mcp_server_url: HttpUrl = "http://127.0.0.1:8000/mcp"
    
    vyzno_cookie_header: SecretStr = Field(min_length=1)
    vyzno_csrf_token: SecretStr = Field(min_length=1)
    vyzno_mailbox_id: UUID4

    gemini_api_key: SecretStr = Field(min_length=1)
    gemini_model: str = "gemini-3.5-flash-lite"