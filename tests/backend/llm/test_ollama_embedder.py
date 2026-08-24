import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.llm.ollama_embedder import OllamaEmbedder
from backend.llm.client import LLMException
from rag.embedder import EmbeddingClient

class TestOllamaEmbedder:
    
    @patch("backend.llm.ollama_embedder.OllamaEmbeddings")
    def test_satisfies_protocol(self, mock_embeddings):
        embedder = OllamaEmbedder()
        assert hasattr(embedder, "embed_texts")
        assert callable(embedder.embed_texts)
        
    @pytest.mark.asyncio
    @patch("backend.llm.ollama_embedder.OllamaEmbeddings")
    async def test_successful_embedding(self, mock_embeddings):
        mock_instance = mock_embeddings.return_value
        mock_instance.aembed_documents = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        
        embedder = OllamaEmbedder()
        result = await embedder.embed_texts(["hello", "world"])
        
        assert len(result) == 2
        assert result[0] == [0.1, 0.2]
        mock_instance.aembed_documents.assert_called_once_with(["hello", "world"])
        
    @pytest.mark.asyncio
    @patch("backend.llm.ollama_embedder.OllamaEmbeddings")
    async def test_embedding_failure_raises_exception(self, mock_embeddings):
        mock_instance = mock_embeddings.return_value
        mock_instance.aembed_documents = AsyncMock(side_effect=Exception("API Error"))
        
        embedder = OllamaEmbedder()
        
        with pytest.raises(LLMException) as exc_info:
            await embedder.embed_texts(["hello"])
            
        assert "Embedding generation failed: API Error" in str(exc_info.value)
        
    @patch("backend.llm.ollama_embedder.OllamaEmbeddings")
    def test_retriever_construction(self, mock_embeddings):
        from rag.retriever import Retriever
        
        embedder = OllamaEmbedder()
        retriever = Retriever(embedder=embedder)
        
        assert retriever.embedder is embedder
