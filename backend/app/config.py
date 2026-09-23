"""Application Configuration using Pydantic Settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./certificates.db", description="Database connection string")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama server URL")
    OLLAMA_MODEL: str = Field(default="llama3.2:latest", description="Ollama model name")
    ALLOWED_ORIGINS: str = Field(default="http://localhost:5173,http://localhost:3000", description="Comma-separated allowed origins")
    HOST: str = Field(default="0.0.0.0", description="FastAPI host")
    PORT: int = Field(default=8000, description="FastAPI port")
    DEBUG: bool = Field(default=True, description="Debug mode")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
