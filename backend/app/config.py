from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://iotdash:iotdash_dev@postgres:5432/iotdash"
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str = "mytoken123"
    INFLUXDB_ORG: str = "iotorg"
    INFLUXDB_BUCKET: str = "iot"
    GRAFANA_URL: str = "http://grafana:3000"
    GRAFANA_ADMIN_USER: str = "admin"
    GRAFANA_ADMIN_PASSWORD: str = "admin"

    MQTT_BROKER_HOST: str = "emqx"
    MQTT_BROKER_PORT: int = 1883

    JWT_SECRET_KEY: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
