"""
Knowledge Repository Versioning and Management
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import chromadb

from backend.schemas import KnowledgeEntry, KnowledgeType
from rag.config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_VALIDATED_KNOWLEDGE
)

class KnowledgeRepository:
    """
    Manages the versioning and storage logic for the Organizational Knowledge Repository.
    Utilizes ChromaDB metadata for version semantics.
    """

    def __init__(self, chroma_client: chromadb.ClientAPI | None = None):
        if chroma_client is None:
            self.chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            self.chroma = chroma_client
            
        self.collection = self.chroma.get_or_create_collection(name=COLLECTION_VALIDATED_KNOWLEDGE)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def store_entry(self, entry: KnowledgeEntry, embedding: List[float]) -> str:
        """
        Stores or updates a knowledge entry. Handles versioning via metadata.
        Returns the specific chunk ID used in ChromaDB.
        """
        # Determine current version
        existing = self.collection.get(
            where={"knowledge_id": entry.id},
            include=["metadatas"]
        )
        
        current_version = 0
        if existing and existing["metadatas"]:
            # Find the highest version among existing metadata
            for meta in existing["metadatas"]:
                if meta and "version" in meta:
                    current_version = max(current_version, int(meta["version"]))

        new_version = current_version + 1
        chunk_id = f"{entry.id}_v{new_version}"

        metadata = {
            "knowledge_id": entry.id,
            "version": new_version,
            "created_at": entry.created_at.isoformat(),
            "updated_at": self._now_iso(),
            "source": f"{entry.source_project_id}/{entry.source_task_id}",
            "domain": "general", # Should be extracted or provided
            "knowledge_type": entry.type.value,
            "validation_status": "validated" if entry.validated else "pending"
        }

        # Add tags to metadata explicitly if needed (chroma limits list types, so join them)
        if entry.tags:
            metadata["tags"] = ",".join(entry.tags)

        self.collection.add(
            ids=[chunk_id],
            documents=[entry.content],
            embeddings=[embedding],
            metadatas=[metadata]
        )

        return chunk_id
