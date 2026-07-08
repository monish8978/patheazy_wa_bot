from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+aiomysql://bob_user:bob_password@localhost:3306/bob_db"
    DATABASE_SYNC_URL: str = "mysql+pymysql://bob_user:bob_password@localhost:3306/bob_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    HOST: str = "0.0.0.0"
    PORT: int = 9103
    DEBUG: bool = True



    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
