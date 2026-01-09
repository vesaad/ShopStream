from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://admin:admin123@mongodb:27017/"  # <-- shiko mongodb, jo mongo
    KAFKA_BROKER: str = "kafka:29092"  # Nëse po përdor docker-compose network

    class Config:
        env_file = ".env"

settings = Settings()
