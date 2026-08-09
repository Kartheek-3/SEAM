"""
SEAM Backend Schemas — Knowledge Context

Retrieved RAG context provided to agents. Wraps similarity search
results from ChromaDB into a structured format.

Source: docs/09_data_models.md §4 (RAGResult, RAGChunk)
Traceability: FR-3.3, FR-3.4
"""

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    """A single chunk of retrieved knowledge from the RAG pipeline."""

    content: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    source: str
    metadata: dict[str, object] = {}


class KnowledgeContext(BaseModel):
    """
    Aggregated RAG retrieval results provided to an agent.

    Carries pre-fetched knowledge context so agents receive relevant
    information from ChromaDB without needing to call RAG directly.
    Agents may still query RAG independently via query_knowledge().
    """

    query: str
    chunks: list[KnowledgeChunk] = []
    total_results: int = Field(default=0, ge=0)
    retrieval_time_ms: int = Field(default=0, ge=0)
