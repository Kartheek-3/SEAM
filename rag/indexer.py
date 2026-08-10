"""
Document Indexer
"""

import hashlib
import logging
import uuid
from typing import List, Dict, Any

import chromadb

from rag.chunker import Chunker
from rag.embedder import EmbeddingClient
from rag.config import CHROMA_PERSIST_DIR, COLLECTION_PROJECT_DOCS

logger = logging.getLogger(__name__)

class Indexer:
    """
    Manages the ingestion pipeline: chunk -> embed -> store in ChromaDB.
    """

    def __init__(self, embedder: EmbeddingClient, chroma_client: chromadb.ClientAPI | None = None):
        self.embedder = embedder
        self.chunker = Chunker()
        
        if chroma_client is None:
            self.chroma = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        else:
            self.chroma = chroma_client

    def _generate_content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def ingest_document(
        self, 
        content: str, 
        source: str, 
        collection_name: str = COLLECTION_PROJECT_DOCS,
        metadata: Dict[str, Any] | None = None
    ) -> int:
        """
        Ingests a raw document into the specified collection.
        Returns the number of chunks indexed.
        """
        collection = self.chroma.get_or_create_collection(name=collection_name)
        
        chunks = self.chunker.split_text(content)
        if not chunks:
            logger.warning(f"No valid chunks generated from {source}")
            return 0

        # Handle embedding
        try:
            embeddings = await self.embedder.embed_texts(chunks)
        except Exception as e:
            logger.error(f"Failed to embed chunks for {source}: {e}")
            return 0

        base_metadata = metadata or {}
        base_metadata["source"] = source
        
        ids = []
        metadatas = []
        valid_chunks = []
        valid_embeddings = []

        doc_uuid = str(uuid.uuid4())

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_hash = self._generate_content_hash(chunk)
            
            # Simple deduplication: Check if hash exists in this collection
            # (Note: In production, checking all metadatas might be slow, but this is a prototype)
            existing = collection.get(where={"content_hash": chunk_hash}, include=[])
            if existing and existing["ids"]:
                logger.info(f"Skipping duplicate chunk in {source}")
                continue
                
            chunk_id = f"{doc_uuid}_chunk_{i}"
            chunk_metadata = base_metadata.copy()
            chunk_metadata["content_hash"] = chunk_hash
            chunk_metadata["chunk_index"] = i
            
            ids.append(chunk_id)
            valid_chunks.append(chunk)
            valid_embeddings.append(emb)
            metadatas.append(chunk_metadata)

        if ids:
            collection.add(
                ids=ids,
                documents=valid_chunks,
                embeddings=valid_embeddings,
                metadatas=metadatas
            )
            logger.info(f"Ingested {len(ids)} chunks from {source} into {collection_name}")
            
        return len(ids)
