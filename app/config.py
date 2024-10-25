from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    client_url: str
    stripe_key: str
    stripe_webhook_secret: str
    env: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
