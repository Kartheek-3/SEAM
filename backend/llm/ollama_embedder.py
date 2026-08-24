"""
Ollama Embedder Implementation

Implements the EmbeddingClient protocol using LangChain's Ollama bindings.
"""

import logging
from typing import List

from langchain_community.embeddings import OllamaEmbeddings

from backend.llm.client import LLMException
from backend.config import settings
from rag.embedder import EmbeddingClient

logger = logging.getLogger(__name__)

class OllamaEmbedder:
    """
    Ollama-backed implementation of the EmbeddingClient Protocol.
    Uses LangChain to retrieve embeddings from the local Ollama instance.
    """

    def __init__(self, model_name: str = settings.ollama_model_embedding):
        self.model_name = model_name
        try:
            self.embedder = OllamaEmbeddings(
                base_url=settings.ollama_base_url,
                model=self.model_name,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Ollama Embeddings: {e}")
            raise LLMException(f"Ollama Embeddings initialization failed: {e}")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of text strings.
        """
        try:
            logger.debug(f"Generating embeddings with Ollama model {self.model_name}")
            return await self.embedder.aembed_documents(texts)
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise LLMException(f"Embedding generation failed: {e}")
