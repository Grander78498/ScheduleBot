from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    api_id: int
    api_hash: SecretStr
    host: str = '127.0.0.1'
    port: str = '5432'
    user: str = 'postgres'
    password: str = 'postgres'
    dbname: str = 'project_db'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()
