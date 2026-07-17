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
    LIVE_AGENT_ACTION_ID: str = "9999.5006"

    # CRM Settings
    CRM_CLIENT_ID: str = "OAqnjdBKVy0TXy2AZoKjkIPIhsOACGg7MWcffQjNVy0"
    CRM_AUTH_TOKEN: str = "xLncDlwuzwzGNHo"
    CRM_API_URL: str = "https://crm.c-zentrix.com/CZCRM/api/AddLeadapi.php"

    # Logging Settings
    LOG_FILE_NAME: str = "patheazy.log"
    LOG_FILE_PATH: str = "/var/log/czentrix"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
