from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "TalentAI"
    APP_VERSION: str = "0.1"

    # TODO: Add your settings here

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
