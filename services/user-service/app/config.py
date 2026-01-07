from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DB_SERVER: str = "localhost"
    DB_USER: str = "SA"
    DB_PASSWORD: str = "YourStrong@Passw0rd"
    DB_NAME: str = "ShopStreamDB"
    
    # Kafka
    KAFKA_BROKER: str = "localhost:9092"
    
    # JWT
    SECRET_KEY: str = "shopstream-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()