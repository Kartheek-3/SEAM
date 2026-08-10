"""
SEAM RAG Package
"""

from .config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    COLLECTION_PROJECT_DOCS,
    COLLECTION_CODE_PATTERNS,
    COLLECTION_ARCHITECTURE,
    COLLECTION_VALIDATED_KNOWLEDGE,
)
from .chunker import Chunker
from .embedder import EmbeddingClient
from .indexer import Indexer
from .retriever import Retriever

__all__ = [
    "Chunker",
    "EmbeddingClient",
    "Indexer",
    "Retriever",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
    "DEFAULT_TOP_K",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "COLLECTION_PROJECT_DOCS",
    "COLLECTION_CODE_PATTERNS",
    "COLLECTION_ARCHITECTURE",
    "COLLECTION_VALIDATED_KNOWLEDGE"
]
