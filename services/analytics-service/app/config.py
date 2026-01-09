from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB configuration for Docker
    MONGO_URI: str = "mongodb://admin:admin123@mongodb:27017/"
    
    # Kafka configuration
    KAFKA_BROKER: str = "kafka:29092"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

print("Config loaded: MONGO_URI=" + settings.MONGO_URI[:30] + "...")
