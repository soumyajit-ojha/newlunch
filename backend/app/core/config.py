from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB Configuration
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str = "5432"
    DB_NAME: str

    # JWT Security
    SECRET_KEY: str  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET_NAME: str

    # Stripe Configuration
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # Payment Gateway
    # PAYMENT_GATEWAY_URL: str
    # PAYMENT_GATEWAY_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
