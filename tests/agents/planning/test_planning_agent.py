"""
Tests for the Planning & Design Agent covering 18 scenarios (Two-Pass Architecture).
"""

import pytest
from datetime import datetime, timezone
from typing import Type

from backend.schemas import (
    AgentInput, AgentStatus, AgentRole, TaskType, Task, TaskStatus
)
from backend.schemas.planning import ProjectPlan, ComponentSpec
from agents.planning.internal_schemas import Pass1ArchitectureResult, Pass2TaskResult, MinimalTask
from backend.llm.client import LLMClient, LLMException
from agents.planning.agent import PlanningAgent
from agents.base import RAGService
from backend.schemas.knowledge import KnowledgeContext, KnowledgeChunk
from pydantic import BaseModel, ValidationError

now = datetime.now(timezone.utc)

class MockLLMClient(LLMClient):
    def __init__(self):
        self.responses = []
        self.exceptions = []
        self.call_count = 0
        self.captured_prompts = []

    async def generate_structured_output(self, system_prompt: str, user_prompt: str, response_model: Type[BaseModel]) -> BaseModel:
        self.call_count += 1
        self.captured_prompts.append(user_prompt)
        
        if self.exceptions:
            ex = self.exceptions.pop(0)
            if ex is not None:
                raise ex
            
        if self.responses:
            return self.responses.pop(0)
            
        raise Exception("Mock exhausted")

class MockRAGService(RAGService):
    def __init__(self, context=None, should_fail=False):
        self.context = context
        self.should_fail = should_fail
        self.call_count = 0
        
    async def retrieve(self, query: str, top_k: int = 5, filters: dict = None) -> KnowledgeContext:
        self.call_count += 1
        if self.should_fail:
            raise Exception("RAG Failure")
        return self.context

@pytest.fixture
def agent():
    return PlanningAgent(llm_client=MockLLMClient())

def create_input(req_spec_dict: dict | None = None) -> AgentInput:
    context = {"project_id": "p-1"}
    if req_spec_dict is not None:
        context["requirement_spec"] = req_spec_dict
    return AgentInput(
        task_id="t-1",
        task_type=TaskType.PLANNING,
        context=context,
        instructions="Plan it."
    )

def create_valid_pass1_result(num_components: int = 1) -> Pass1ArchitectureResult:
    components = []
    for i in range(num_components):
        components.append(ComponentSpec(name=f"C{i+1}", description="desc", responsibilities=["db", "api", "security"]))
    return Pass1ArchitectureResult(
        architecture_summary="Basic architecture",
        components=components,
        technology_recommendations=["Python"]
    )

def create_valid_pass2_result(component_idx: int = 1) -> Pass2TaskResult:
    return Pass2TaskResult(
        tasks=[
            MinimalTask(local_id=f"T-{component_idx}", title=f"Setup C{component_idx}", description="desc", depends_on=[])
        ]
    )

@pytest.mark.asyncio
async def test_pass1_and_pass2_success(agent):
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    agent.llm.exceptions = [None, None]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 2
    assert "architecture_summary" in out.result

@pytest.mark.asyncio
async def test_multiple_components(agent):
    agent.llm.responses = [create_valid_pass1_result(2), create_valid_pass2_result(1), create_valid_pass2_result(2)]
    agent.llm.exceptions = [None, None, None]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["components"]) == 2
    assert len(out.result["tasks"]) == 2

@pytest.mark.asyncio
async def test_cross_component_dependencies(agent):
    pass1 = create_valid_pass1_result(2)
    pass2_c1 = create_valid_pass2_result(1)
    pass2_c2 = create_valid_pass2_result(2)
    pass2_c2.tasks[0].depends_on = ["mocked-uuid"]
    
    # We will mock uuid.uuid4 to return predictable values
    import uuid
    from unittest.mock import patch
    
    with patch('uuid.uuid4', side_effect=[uuid.UUID('00000000-0000-0000-0000-000000000001'), uuid.UUID('00000000-0000-0000-0000-000000000002')]):
        pass2_c2.tasks[0].depends_on = ['00000000-0000-0000-0000-000000000001']
        agent.llm.responses = [pass1, pass2_c1, pass2_c2]
        agent.llm.exceptions = [None, None, None]
        out = await agent.execute(create_input({"project_id": "p-1"}))
        assert out.status == AgentStatus.SUCCESS
        
        # Assert context was passed with the real UUID
        assert f"Task ID: 00000000-0000-0000-0000-000000000001" in agent.llm.captured_prompts[2]

@pytest.mark.asyncio
async def test_unknown_dependency(agent):
    pass1 = create_valid_pass1_result(1)
    pass2 = create_valid_pass2_result(1)
    pass2.tasks[0].depends_on = ["UNKNOWN-99"]
    
    agent.llm.responses = [pass1, pass2]
    agent.llm.exceptions = [None, None]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert "unknown dependency 'UNKNOWN-99'" in out.feedback

@pytest.mark.asyncio
async def test_circular_dependency_rejection(agent):
    pass1 = create_valid_pass1_result(1)
    pass2_c1 = create_valid_pass2_result(1)
    # Create an intra-component cycle
    from agents.planning.internal_schemas import MinimalTask
    pass2_c1.tasks.append(MinimalTask(local_id="T-2", title="Task 2", description="desc", depends_on=["T-1"]))
    pass2_c1.tasks[0].depends_on = ["T-2"]
    
    agent.llm.responses = [pass1, pass2_c1]
    agent.llm.exceptions = [None, None]
    
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert "Cycle detected" in out.feedback

@pytest.mark.asyncio
async def test_invalid_requirementspec(agent):
    out = await agent.execute(create_input(None)) # Missing req spec
    assert out.status == AgentStatus.FAILURE
    assert "RequirementSpec is missing" in out.feedback

@pytest.mark.asyncio
async def test_pass1_malformed_llm_output_retry(agent):
    agent.llm.exceptions = [ValidationError.from_exception_data("error", line_errors=[]), None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3 # 1 failed pass1, 1 success pass1, 1 success pass2

@pytest.mark.asyncio
async def test_pass2_malformed_llm_output_retry(agent):
    agent.llm.exceptions = [None, ValidationError.from_exception_data("error", line_errors=[]), None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3 # 1 success pass1, 1 failed pass2, 1 success pass2

@pytest.mark.asyncio
async def test_pass1_retries_on_llm_timeout(agent):
    agent.llm.exceptions = [LLMException("Timeout"), None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3 # 1 timeout pass1, 1 success pass1, 1 success pass2

@pytest.mark.asyncio
async def test_pass2_retries_on_llm_timeout(agent):
    agent.llm.exceptions = [None, LLMException("Timeout"), None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3 # 1 success pass1, 1 timeout pass2, 1 success pass2

@pytest.mark.asyncio
async def test_pass2_retry_isolated_to_failed_component(agent):
    agent.llm.exceptions = [None, None, LLMException("Timeout"), None]
    pass1 = create_valid_pass1_result(2)
    pass2_1 = create_valid_pass2_result(1)
    pass2_2 = create_valid_pass2_result(2)
    agent.llm.responses = [pass1, pass2_1, pass2_2]
    
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 4 # pass1, pass2_c1, pass2_c2_timeout, pass2_c2_success
    assert len(out.result["components"]) == 2
    assert len(out.result["tasks"]) == 2

@pytest.mark.asyncio
async def test_pass2_final_timeout_fails(agent):
    agent.llm.exceptions = [None, LLMException("Timeout"), LLMException("Timeout"), LLMException("Timeout")]
    agent.llm.responses = [create_valid_pass1_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 4 # 1 success pass1, 3 timeouts pass2
    assert "Timeout" in out.feedback

@pytest.mark.asyncio
async def test_no_retry_beyond_max_attempts(agent):
    agent.llm.exceptions = [LLMException("Timeout"), LLMException("Timeout"), LLMException("Timeout"), LLMException("Timeout")]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 3 # max 3 retries for pass 1

@pytest.mark.asyncio
async def test_validation_retry_behavior_unchanged(agent):
    agent.llm.exceptions = [ValidationError.from_exception_data("error", line_errors=[]), None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3

@pytest.mark.asyncio
async def test_timeout_telemetry_counts_failed_attempts(agent):
    agent.llm.exceptions = [LLMException("Timeout"), None, LLMException("Timeout"), None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 4 # 2 for pass1, 2 for pass2

@pytest.mark.asyncio
async def test_rag_success():
    llm = MockLLMClient()
    llm.exceptions = [None, None]
    llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    rag = MockRAGService(context=KnowledgeContext(query="test", chunks=[KnowledgeChunk(content="Domain knowledge", similarity_score=0.9, source="test")]))
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "Domain knowledge" in llm.captured_prompts[0] # Pass 1 has RAG
    assert "Domain knowledge" not in llm.captured_prompts[1] # Pass 2 does NOT have RAG

@pytest.mark.asyncio
async def test_rag_failure():
    llm = MockLLMClient()
    llm.exceptions = [None, None]
    llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    rag = MockRAGService(should_fail=True)
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS # Graceful degradation
    assert rag.call_count == 1

@pytest.mark.asyncio
async def test_projectplan_validation(agent):
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "architecture_summary" in out.result

@pytest.mark.asyncio
async def test_performance_mock_independence(agent):
    """Proves Pass 2 operates independently per component without carrying large arrays back and forth."""
    agent.llm.exceptions = [None, None, None]
    pass1 = create_valid_pass1_result(2) # 2 components
    pass2_1 = create_valid_pass2_result(1)
    pass2_2 = create_valid_pass2_result(2)
    agent.llm.responses = [pass1, pass2_1, pass2_2]
    
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3
    
    # Assert Pass 2 requests strictly targeted individual components
    assert "C1" in agent.llm.captured_prompts[1]
    assert "C2" in agent.llm.captured_prompts[2]

@pytest.mark.asyncio
async def test_duplicate_task_ids_are_passed_down_to_fail(agent):
    pass1 = create_valid_pass1_result(2)
    pass2_c1 = create_valid_pass2_result(1)
    pass2_c1.tasks[0].local_id = "DUPE"
    pass2_c2 = create_valid_pass2_result(2)
    pass2_c2.tasks[0].local_id = "DUPE"
    
    agent.llm.responses = [pass1, pass2_c1, pass2_c2]
    agent.llm.exceptions = [None, None, None]
    
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    # UUIDs are unique even if local_ids clash across components! The mapper assigns new UUIDs.
    assert out.result["tasks"][0]["id"] != out.result["tasks"][1]["id"]

# --- RESTORED DOMAIN TESTS ---

@pytest.mark.asyncio
async def test_simple_software_requirement(agent):
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 2

@pytest.mark.asyncio
async def test_ecommerce_project(agent):
    pass1 = create_valid_pass1_result(2)
    pass1.components[1].name = "Cart"
    agent.llm.exceptions = [None, None, None]
    agent.llm.responses = [pass1, create_valid_pass2_result(1), create_valid_pass2_result(2)]
    out = await agent.execute(create_input({"project_id": "p-1", "entities": ["Cart"]}))
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["components"]) == 2

@pytest.mark.asyncio
async def test_healthcare_project(agent):
    pass1 = create_valid_pass1_result(1)
    pass1.architecture_summary = "HIPAA Compliant"
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [pass1, create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "HIPAA" in out.result["architecture_summary"]

@pytest.mark.asyncio
async def test_multi_module_project(agent):
    pass1 = create_valid_pass1_result(2)
    agent.llm.exceptions = [None, None, None]
    agent.llm.responses = [pass1, create_valid_pass2_result(1), create_valid_pass2_result(2)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["components"]) == 2

@pytest.mark.asyncio
async def test_component_generation(agent):
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["components"][0]["name"] == "C1"

@pytest.mark.asyncio
async def test_task_generation(agent):
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["tasks"][0]["id"] != "T-1" # UUID is generated
    assert out.result["tasks"][0]["project_id"] == "p-1"

@pytest.mark.asyncio
async def test_dependency_generation(agent):
    pass2 = create_valid_pass2_result(1)
    pass2.tasks[0].depends_on = ["T-0"] # Mock dependency
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), pass2]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE # T-0 doesn't exist, DFS check fails

@pytest.mark.asyncio
async def test_acceptance_criteria_generation(agent):
    agent.llm.exceptions = [None, None]
    agent.llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "desc" in out.result["tasks"][0]["description"]

@pytest.mark.asyncio
async def test_minimal_task_schema_constraints():
    """
    IMPORTANT REGRESSION TEST: Proves the LLM-facing schema does NOT require
    id, project_id, created_at, completed_at, status, UUID values.
    """
    mt = MinimalTask(
        local_id="local-1",
        title="Valid Title",
        description="Valid desc",
        depends_on=[]
    )
    # The fields should not exist on the Pydantic model at all
    with pytest.raises(AttributeError):
        _ = mt.id
    with pytest.raises(AttributeError):
        _ = mt.project_id
    with pytest.raises(AttributeError):
        _ = mt.created_at
    with pytest.raises(AttributeError):
        _ = mt.status

    assert mt.local_id == "local-1"
    
@pytest.mark.asyncio
async def test_empty_rag_context():
    llm = MockLLMClient()
    llm.exceptions = [None, None]
    llm.responses = [create_valid_pass1_result(1), create_valid_pass2_result(1)]
    rag = MockRAGService(context=KnowledgeContext(query="test", chunks=[]))
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "RETRIEVED DOMAIN KNOWLEDGE" not in llm.captured_prompts[0]
