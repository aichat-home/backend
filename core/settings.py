from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_url: str
    db_echo: bool
    telegram_token: str
    telegram_channel_id: str
    webapp_url: str
    admin_username: str
    admin_password: str
    farm_seconds: int
    farm_reward: int

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )


settings = Settings()