from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MS SQL Database configuration for Docker
    DB_SERVER: str = "mssql"
    DB_USER: str = "SA"
    DB_PASSWORD: str = "YourStrong@Passw0rd"
    DB_NAME: str = "ShopStreamDB"
    
    # Kafka configuration
    KAFKA_BROKER: str = "kafka:29092"
    
    # Product Service URL
    PRODUCT_SERVICE_URL: str = "http://product-service:8002"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Debug log
print("Config loaded: DB_SERVER=" + settings.DB_SERVER)