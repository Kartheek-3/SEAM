"""
RAG Configuration
"""

from backend.config import settings

# ChromaDB Config
CHROMA_PERSIST_DIR = settings.chroma_persist_dir

# Chunking Defaults
DEFAULT_CHUNK_SIZE = settings.rag_chunk_size
DEFAULT_CHUNK_OVERLAP = settings.rag_chunk_overlap

# Retrieval Defaults
DEFAULT_TOP_K = settings.rag_top_k
DEFAULT_SIMILARITY_THRESHOLD = settings.rag_similarity_threshold

# Collection Names
COLLECTION_PROJECT_DOCS = "project_docs"
COLLECTION_CODE_PATTERNS = "code_patterns"
COLLECTION_ARCHITECTURE = "architecture"
COLLECTION_VALIDATED_KNOWLEDGE = "validated_knowledge"

ALL_COLLECTIONS = [
    COLLECTION_PROJECT_DOCS,
    COLLECTION_CODE_PATTERNS,
    COLLECTION_ARCHITECTURE,
    COLLECTION_VALIDATED_KNOWLEDGE
]
