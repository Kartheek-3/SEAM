import pytest
from unittest.mock import patch, AsyncMock
from backend.llm.ollama_client import OllamaClient
from backend.llm.client import LLMException
from pydantic import BaseModel

class DummyModel(BaseModel):
    name: str

@pytest.mark.asyncio
async def test_ollama_client_timeout_handling():
    client = OllamaClient(model_name="test")
    
    with patch("langchain_core.runnables.RunnableSequence.ainvoke", new_callable=AsyncMock) as mock_chain_ainvoke:
        mock_chain_ainvoke.side_effect = TimeoutError()
        
        with pytest.raises(LLMException) as exc_info:
            await client.generate_structured_output("sys", "user", DummyModel)
            
        assert "timed out" in str(exc_info.value)
