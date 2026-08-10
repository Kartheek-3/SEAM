"""
Tests for Knowledge Repository Versioning
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock

from backend.schemas import KnowledgeEntry, KnowledgeType
from knowledge.repository import KnowledgeRepository
from rag.config import COLLECTION_VALIDATED_KNOWLEDGE

@pytest.fixture
def repo():
    # Mock client
    client = MagicMock()
    mock_collection = MagicMock()
    
    # First get returns no existing metadata (v0 -> v1)
    # Second get returns metadata with version 1 (v1 -> v2)
    mock_collection.get.side_effect = [
        {"metadatas": []},
        {"metadatas": [{"version": 1, "knowledge_type": "code_pattern"}]}
    ]
    
    client.get_or_create_collection.return_value = mock_collection
    client.get_collection.return_value = mock_collection
    return KnowledgeRepository(chroma_client=client)

def test_knowledge_versioning(repo):
    entry = KnowledgeEntry(
        id="k-1",
        source_project_id="p-1",
        source_task_id="t-1",
        type=KnowledgeType.CODE_PATTERN,
        title="Test Entry",
        content="Code content",
        created_at=datetime.now(timezone.utc),
        validated=True
    )
    
    # Store initial version
    embedding = [0.1, 0.2]
    chunk_id_v1 = repo.store_entry(entry, embedding)
    
    assert chunk_id_v1 == "k-1_v1"
    
    # Skip deep query checks since we are mocking
    # Just verify the repository generates the right ID based on mock returns
    
    # Store updated version
    chunk_id_v2 = repo.store_entry(entry, embedding)
    assert chunk_id_v2 == "k-1_v2"
