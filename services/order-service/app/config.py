from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_SERVER: str = "localhost"
    DB_USER: str = "SA"
    DB_PASSWORD: str = "YourStrong@Passw0rd"
    DB_NAME: str = "ShopStreamDB"

    KAFKA_BROKER: str = "localhost:9092"
    PRODUCT_SERVICE_URL: str = "http://localhost:8002"

    class Config:
        env_file = ".env"

settings = Settings()
