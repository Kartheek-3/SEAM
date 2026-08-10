"""
Embedder Abstraction
"""

from typing import Protocol, List

class EmbeddingClient(Protocol):
    """
    Protocol defining the required interface for embedding models.
    Ensures that the embedding model can be replaced without changing
    the core RAG architecture.
    """

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of text strings.

        Args:
            texts: List of strings to embed.

        Returns:
            List of embedding vectors (list of floats).
        """
        ...
