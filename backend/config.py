import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/education_platform")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_PRIMARY_MODEL: str = os.getenv("GROQ_PRIMARY_MODEL", "openai/gpt-oss-20b")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-120b")
    GROQ_TIMEOUT_SECONDS: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30"))
    GROQ_MAX_RETRIES: int = min(2, max(0, int(os.getenv("GROQ_MAX_RETRIES", "1"))))
    GROQ_MAX_TOKENS: int = min(8192, max(256, int(os.getenv("GROQ_MAX_TOKENS", "2048"))))
    APP_ENV: str = os.getenv("APP_ENV", "production" if os.getenv("RENDER") else "development")
    APP_URL: str = os.getenv("APP_URL", os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000"))
    COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", str(APP_ENV == "production")).lower() == "true"
    ALLOWED_ORIGINS: list = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", APP_URL).split(",") if origin.strip()]
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
    MONGO_CONNECT_TIMEOUT_MS: int = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))
    MONGO_SOCKET_TIMEOUT_MS: int = int(os.getenv("MONGO_SOCKET_TIMEOUT_MS", "10000"))
    MONGO_WAIT_QUEUE_TIMEOUT_MS: int = int(os.getenv("MONGO_WAIT_QUEUE_TIMEOUT_MS", "5000"))
    MONGO_OPERATION_TIMEOUT_MS: int = int(os.getenv("MONGO_OPERATION_TIMEOUT_MS", "15000"))
    MONGO_PING_TIMEOUT_MS: int = int(os.getenv("MONGO_PING_TIMEOUT_MS", "2000"))
    PISTON_EXECUTE_URL: str = os.getenv("PISTON_EXECUTE_URL", "")
    PISTON_API_KEY: str = os.getenv("PISTON_API_KEY", "")
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "60"))
    AUTH_RATE_LIMIT: int = int(os.getenv("AUTH_RATE_LIMIT", "10"))
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "auto")
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "") or os.getenv("bravo_key", "")
    RESET_PASSWORD_BASE_URL: str = os.getenv("RESET_PASSWORD_BASE_URL", APP_URL)
    
    # Port to run FastAPI
    PORT: int = int(os.getenv("PORT", 8000))
    
    # SMTP Settings for Password Reset
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")

settings = Settings()
