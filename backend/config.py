"""
SEAM Central Configuration Manager

Loads and validates environment variables using pydantic-settings.
Provides a central, type-safe configuration object for the framework.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """
    Central Configuration Settings.
    Automatically loads from environment variables or a .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore unmapped variables from .env
    )

    # Application
    app_name: str = "SEAM"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # LLM Settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model_coding: str = "deepseek-coder"
    ollama_model_general: str = "llama3.1"
    ollama_timeout: int = 120

    # ChromaDB / RAG
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./knowledge/data"
    chroma_collection_name: str = "seam_knowledge"
    
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7

    # Security
    secret_key: str = "change-me-in-production"
    api_key: Optional[str] = None


# Instantiate a global configuration object
settings = AppConfig()
