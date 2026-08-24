"""
SEAM Central Configuration Manager

Loads and validates environment variables using pydantic-settings.
Provides a central, type-safe configuration object for the framework.
"""

import json
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


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
    ollama_model_embedding: str = "nomic-embed-text"
    ollama_timeout: int = 120
    ollama_workers: str = "" # JSON string

    @field_validator("ollama_workers")
    @classmethod
    def validate_ollama_workers(cls, v: str) -> str:
        if not v:
            return v
        try:
            workers = json.loads(v)
            if not isinstance(workers, list):
                raise ValueError("OLLAMA_WORKERS must be a JSON array")
            
            seen_ids = set()
            seen_endpoints = set()
            for w in workers:
                if "worker_id" not in w:
                    raise ValueError("Worker missing 'worker_id'")
                if "host" not in w or "port" not in w:
                    raise ValueError("Worker missing 'host' or 'port'")
                if "model" not in w:
                    raise ValueError("Worker missing 'model'")
                
                if w["worker_id"] in seen_ids:
                    raise ValueError(f"Duplicate worker_id: {w['worker_id']}")
                seen_ids.add(w["worker_id"])
                
                endpoint = f"{w['host']}:{w['port']}"
                if endpoint in seen_endpoints:
                    raise ValueError(f"Duplicate endpoint: {endpoint}")
                seen_endpoints.add(endpoint)
                
            return v
        except json.JSONDecodeError:
            raise ValueError("OLLAMA_WORKERS must be a valid JSON string")

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
