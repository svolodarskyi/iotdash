from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://iotdash:iotdash_dev@postgres:5432/iotdash"
    INFLUXDB_URL: str = "http://influxdb:8086"
    INFLUXDB_TOKEN: str = "mytoken123"
    INFLUXDB_ORG: str = "iotorg"
    INFLUXDB_BUCKET: str = "iot"
    GRAFANA_URL: str = "http://grafana:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
