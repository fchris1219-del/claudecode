from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ntfy_base_url: str = "https://ntfy.sh"
    ntfy_default_topic: str = "myphone-changeme"
    ntfy_auth_token: str = ""

    api_key: str = "change-me-long-random-string"

    server_host: str = "0.0.0.0"
    server_port: int = 8000

    db_path: str = "./todos.db"
    timezone: str = "Asia/Shanghai"

    anthropic_api_key: str = ""

    # Default cron schedules (overridable per-routine in DB)
    evening_prompt_cron: str = "0 21 * * *"   # 9pm
    morning_search_cron: str = "0 8 * * *"    # 8am


settings = Settings()
