"""
Tests for RAG Indexer and Retriever
"""

import pytest
from unittest.mock import MagicMock
from typing import List

from rag.indexer import Indexer
from rag.retriever import Retriever
from rag.embedder import EmbeddingClient
from rag.config import COLLECTION_PROJECT_DOCS

class MockEmbedder(EmbeddingClient):
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        # Return a simple mock embedding vector for each text
        return [[0.1, 0.2, 0.3] for _ in texts]

@pytest.fixture
def chroma_client():
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock for retrieval
    mock_collection.query.return_value = {
        "documents": [["Doc 1 text"]],
        "metadatas": [[{"source": "test_doc.md", "domain": "architecture", "type": "arch"}]],
        "distances": [[0.1]]
    }
    
    # Mock for ingestion duplicate check
    mock_collection.get.side_effect = [
        {"ids": []}, # First call: no duplicates
        {"ids": ["existing_id"]} # Second call: has duplicates
    ]
    
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client.get_collection.return_value = mock_collection
    
    return mock_client

@pytest.fixture
def indexer(chroma_client):
    return Indexer(embedder=MockEmbedder(), chroma_client=chroma_client)

@pytest.fixture
def retriever(chroma_client):
    return Retriever(embedder=MockEmbedder(), chroma_client=chroma_client)

@pytest.mark.asyncio
async def test_ingest_and_retrieve(indexer, retriever, chroma_client):
    content = "This is a test document about SEAM architecture. " * 50
    
    # 1. Test Ingestion
    chunks_indexed = await indexer.ingest_document(
        content=content,
        source="test_doc.md",
        metadata={"domain": "architecture", "knowledge_type": "architecture_pattern"}
    )
    assert chunks_indexed > 0
    
    # Verify duplicates are skipped
    chunks_indexed_dup = await indexer.ingest_document(
        content=content,
        source="test_doc.md",
        metadata={"domain": "architecture", "knowledge_type": "architecture_pattern"}
    )
    assert chunks_indexed_dup == 0
    
    # 2. Test Retrieval
    context = await retriever.retrieve(
        query="architecture",
        collection_name=COLLECTION_PROJECT_DOCS,
        top_k=2,
        similarity_threshold=0.0 # Allow all for the mock
    )
    
    assert context.total_results > 0
    assert context.chunks[0].source == "test_doc.md"
    assert context.chunks[0].metadata["domain"] == "architecture"

@pytest.mark.asyncio
async def test_retriever_empty_repository(retriever, chroma_client):
    # Mock collection throwing exception for non-existent
    chroma_client.get_collection.side_effect = Exception("Collection not found")
    context = await retriever.retrieve("query", collection_name="non_existent")
    assert context.total_results == 0
    assert len(context.chunks) == 0

@pytest.mark.asyncio
async def test_retriever_filtering(indexer, retriever, chroma_client):
    # Reset side effect for normal get
    chroma_client.get_collection.side_effect = None
    
    context = await retriever.retrieve(
        query="test",
        collection_name=COLLECTION_PROJECT_DOCS,
        metadata_filters={"type": "arch"}
    )
    
    assert context.total_results > 0
    assert context.chunks[0].metadata["type"] == "arch"
