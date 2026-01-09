from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database configuration for Docker
    DB_SERVER: str = "mssql"
    DB_USER: str = "SA"
    DB_PASSWORD: str = "YourStrong@Passw0rd"
    DB_NAME: str = "ShopStreamDB"
    
    # Kafka configuration
    KAFKA_BROKER: str = "kafka:29092"
    
    # JWT configuration
    SECRET_KEY: str = "your-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Debug log
print("Config loaded: DB_SERVER=" + settings.DB_SERVER)
