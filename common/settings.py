import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = pathlib.Path(__file__).parent.parent


class Settings(BaseSettings):
    debug: bool = True
    string_connect: str = "mongodb://localhost:27017/casher_database"

    # model_config = SettingsConfigDict(
    #     env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    # )


settings = Settings()
