import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/education_platform")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-replace-in-production-123456")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_PRIMARY_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_FALLBACK_MODEL: str = "openai/gpt-oss-120b"
    
    # Port to run FastAPI
    PORT: int = int(os.getenv("PORT", 8000))

settings = Settings()
