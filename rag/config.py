"""
RAG Configuration
"""

import os

# ChromaDB Config
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./knowledge/data")

# Chunking Defaults
DEFAULT_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "512"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))

# Retrieval Defaults
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))

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
