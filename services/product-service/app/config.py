from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DB_SERVER: str = "localhost"
    DB_USER: str = "SA"
    DB_PASSWORD: str = "YourStrong@Passw0rd"
    DB_NAME: str = "ShopStreamDB"
    
    # Kafka
    KAFKA_BROKER: str = "localhost:9092"
    
    # Service
    SERVICE_NAME: str = "product-service"
    SERVICE_PORT: int = 8002
    
    class Config:
        env_file = ".env"

settings = Settings()