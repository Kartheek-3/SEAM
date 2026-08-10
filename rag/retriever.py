"""
Similarity Retriever
"""

import time
import logging
from typing import Dict, Any, List

import chromadb

from rag.embedder import EmbeddingClient
from rag.config import (
    CHROMA_PERSIST_DIR,
    DEFAULT_TOP_K,
    DEFAULT_SIMILARITY_THRESHOLD,
    COLLECTION_VALIDATED_KNOWLEDGE
)
from backend.schemas import KnowledgeContext, KnowledgeChunk

logger = logging.getLogger(__name__)

class Retriever:
    """
    Handles similarity search queries from agents and maps results
    to the KnowledgeContext schema.
    """

    def __init__(self, embedder: EmbeddingClient, chroma_client: chromadb.ClientAPI | None = None):
        self.embedder = embedder
        if chroma_client is None:
            self.chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            self.chroma = chroma_client

    async def retrieve(
        self,
        query: str,
        collection_name: str = COLLECTION_VALIDATED_KNOWLEDGE,
        top_k: int = DEFAULT_TOP_K,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        metadata_filters: Dict[str, Any] | None = None
    ) -> KnowledgeContext:
        """
        Retrieves context from ChromaDB based on semantic similarity.
        """
        start_time = time.time()
        
        try:
            collection = self.chroma.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Failed to access collection {collection_name}: {e}")
            return self._empty_context(query)

        try:
            query_embeddings = await self.embedder.embed_texts([query])
            query_embedding = query_embeddings[0]
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return self._empty_context(query)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filters or {},
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return self._empty_context(query)

        if not results or not results.get("documents") or not results["documents"][0]:
            return self._empty_context(query)

        knowledge_chunks = []
        
        # ChromaDB results are lists of lists (one list per query embedding)
        docs = results["documents"][0]
        distances = results["distances"][0] if "distances" in results and results["distances"] else []
        metadatas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []

        for i in range(len(docs)):
            # Convert distance to similarity score (assuming cosine distance where 0 is exact match)
            distance = distances[i] if i < len(distances) else 1.0
            similarity_score = max(0.0, 1.0 - distance)
            
            if similarity_score < similarity_threshold:
                continue
                
            metadata = metadatas[i] if i < len(metadatas) and metadatas[i] else {}
            source = str(metadata.get("source", "unknown"))
            
            chunk = KnowledgeChunk(
                content=docs[i],
                similarity_score=similarity_score,
                source=source,
                metadata=metadata
            )
            knowledge_chunks.append(chunk)

        retrieval_time_ms = int((time.time() - start_time) * 1000)
        
        return KnowledgeContext(
            query=query,
            chunks=knowledge_chunks,
            total_results=len(knowledge_chunks),
            retrieval_time_ms=retrieval_time_ms
        )

    def _empty_context(self, query: str) -> KnowledgeContext:
        """Helper to return an empty context safely."""
        return KnowledgeContext(
            query=query,
            chunks=[],
            total_results=0,
            retrieval_time_ms=0
        )
