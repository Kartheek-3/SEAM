import pytest
from unittest.mock import AsyncMock, MagicMock
from evaluation.runner import TelemetryLLMClient
from backend.llm.client import LLMException

@pytest.mark.asyncio
async def test_telemetry_llm_proxies_generate_structured_output():
    mock_base = MagicMock()
    mock_base.generate_structured_output = AsyncMock(return_value="out")
    client = TelemetryLLMClient(mock_base)
    
    res = await client.generate_structured_output("sys", "user", dict)
    
    assert res == "out"
    assert client.invocation_count == 1
    mock_base.generate_structured_output.assert_called_once_with("sys", "user", dict)

@pytest.mark.asyncio
async def test_telemetry_llm_proxies_generate_structured_response():
    mock_base = MagicMock()
    # It doesn't have generate_structured_response, should fallback to generate_structured_output
    del mock_base.generate_structured_response
    mock_base.generate_structured_output = AsyncMock(return_value="resp")
    
    client = TelemetryLLMClient(mock_base)
    
    res = await client.generate_structured_response("sys", "user", dict)
    
    assert res == "resp"
    assert client.invocation_count == 1
    mock_base.generate_structured_output.assert_called_once_with("sys", "user", dict)

@pytest.mark.asyncio
async def test_telemetry_llm_proxies_generate_structured_response_if_exists():
    mock_base = MagicMock()
    mock_base.generate_structured_response = AsyncMock(return_value="resp2")
    
    client = TelemetryLLMClient(mock_base)
    
    res = await client.generate_structured_response("sys", "user", dict)
    
    assert res == "resp2"
    assert client.invocation_count == 1
    mock_base.generate_structured_response.assert_called_once_with("sys", "user", dict)

@pytest.mark.asyncio
async def test_telemetry_llm_increments_on_failure():
    mock_base = MagicMock()
    mock_base.generate_structured_output = AsyncMock(side_effect=LLMException("Fail"))
    
    client = TelemetryLLMClient(mock_base)
    
    with pytest.raises(LLMException):
        await client.generate_structured_output("sys", "user", dict)
        
    assert client.invocation_count == 1

@pytest.mark.asyncio
async def test_coding_agent_can_operate_with_telemetry_llm():
    from agents.coding.agent import CodingAgent
    from backend.schemas import AgentInput, TaskType, AgentStatus
    from agents.coding.agent import CodeGenerationResponse, GeneratedFile
    from backend.schemas import ArtifactType
    
    class FakeLLMClient:
        async def generate_structured_output(self, *args, **kwargs):
            return CodeGenerationResponse(
                files=[GeneratedFile(path="t.py", content="x", language="python", artifact_type=ArtifactType.CODE)]
            )
            
    mock_base = FakeLLMClient()
    
    client = TelemetryLLMClient(mock_base)
    agent = CodingAgent(llm_client=client)
    res = await agent.execute(AgentInput(task_id="t", task_type=TaskType.CODING, instructions="x", context={}))
    
    assert res.status == AgentStatus.SUCCESS
    assert client.invocation_count >= 1

@pytest.mark.asyncio
async def test_telemetry_llm_no_double_counting():
    """Verify generate_structured_response fallback does not double-count."""
    mock_base = MagicMock()
    del mock_base.generate_structured_response
    mock_base.generate_structured_output = AsyncMock(return_value="val")

    client = TelemetryLLMClient(mock_base)

    await client.generate_structured_response("s", "u", dict)
    await client.generate_structured_output("s", "u", dict)
    await client.generate_structured_response("s", "u", dict)

    assert client.invocation_count == 3
    assert mock_base.generate_structured_output.call_count == 3

@pytest.mark.asyncio
async def test_telemetry_llm_exception_propagated_unchanged():
    """Verify the exact exception object is re-raised, not wrapped."""
    original_exc = LLMException("specific error 42")
    mock_base = MagicMock()
    mock_base.generate_structured_output = AsyncMock(side_effect=original_exc)

    client = TelemetryLLMClient(mock_base)

    with pytest.raises(LLMException) as exc_info:
        await client.generate_structured_output("s", "u", dict)

    assert exc_info.value is original_exc

@pytest.mark.asyncio
async def test_telemetry_llm_generate_structured_response_increments_on_failure():
    """Verify invocation_count increments even when generate_structured_response raises."""
    original_exc = LLMException("response fail")
    mock_base = MagicMock()
    del mock_base.generate_structured_response
    mock_base.generate_structured_output = AsyncMock(side_effect=original_exc)

    client = TelemetryLLMClient(mock_base)

    with pytest.raises(LLMException) as exc_info:
        await client.generate_structured_response("s", "u", dict)

    assert client.invocation_count == 1
    assert exc_info.value is original_exc
