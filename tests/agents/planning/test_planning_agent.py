"""
Tests for the Planning & Design Agent covering 16 scenarios.
"""

import pytest
from datetime import datetime, timezone
from typing import Type

from backend.schemas import (
    AgentInput, AgentStatus, AgentRole, TaskType, Task, TaskStatus
)
from backend.schemas.planning import ProjectPlan, ComponentSpec
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
            raise self.exceptions.pop(0)
            
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

def create_valid_project_plan() -> ProjectPlan:
    return ProjectPlan(
        project_id="p-1",
        architecture_summary="Basic architecture",
        components=[ComponentSpec(name="C1", description="desc", responsibilities=["db", "api", "security"])],
        tasks=[
            Task(id="T-1", project_id="p-1", title="Setup", description="desc", type=TaskType.CODING, created_at=now, input_data={"acceptance_criteria": "Tests pass"})
        ],
        technology_recommendations=["Python"]
    )

@pytest.mark.asyncio
async def test_simple_software_requirement(agent):
    agent.llm.responses = [create_valid_project_plan()]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 1

@pytest.mark.asyncio
async def test_ecommerce_project(agent):
    plan = create_valid_project_plan()
    plan.components.append(ComponentSpec(name="Cart", description="Shopping cart", responsibilities=[]))
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1", "entities": ["Cart"]}))
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["components"]) == 2

@pytest.mark.asyncio
async def test_healthcare_project(agent):
    plan = create_valid_project_plan()
    plan.architecture_summary = "HIPAA Compliant"
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "HIPAA" in out.result["architecture_summary"]

@pytest.mark.asyncio
async def test_multi_module_project(agent):
    plan = create_valid_project_plan()
    plan.components = [
        ComponentSpec(name="ModuleA", description="A", responsibilities=[]),
        ComponentSpec(name="ModuleB", description="B", responsibilities=[])
    ]
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["components"]) == 2

@pytest.mark.asyncio
async def test_component_generation(agent):
    plan = create_valid_project_plan()
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["components"][0]["name"] == "C1"

@pytest.mark.asyncio
async def test_task_generation(agent):
    plan = create_valid_project_plan()
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["tasks"][0]["id"] == "T-1"

@pytest.mark.asyncio
async def test_dependency_generation(agent):
    plan = create_valid_project_plan()
    plan.tasks.append(
        Task(id="T-2", project_id="p-1", title="API", description="API", type=TaskType.CODING, created_at=now, dependencies=["T-1"])
    )
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["tasks"][1]["dependencies"] == ["T-1"]

@pytest.mark.asyncio
async def test_circular_dependency_rejection(agent):
    plan_with_cycle = create_valid_project_plan()
    plan_with_cycle.tasks = [
        Task(id="T-1", project_id="p-1", title="A", description="A", type=TaskType.CODING, created_at=now, dependencies=["T-2"]),
        Task(id="T-2", project_id="p-1", title="B", description="B", type=TaskType.CODING, created_at=now, dependencies=["T-1"])
    ]
    # Provide it 3 times to exhaust retries
    agent.llm.responses = [plan_with_cycle, plan_with_cycle, plan_with_cycle]
    
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert "Failed to generate acyclic task graph" in out.feedback

@pytest.mark.asyncio
async def test_invalid_requirementspec(agent):
    out = await agent.execute(create_input(None)) # Missing req spec
    assert out.status == AgentStatus.FAILURE
    assert "RequirementSpec is missing" in out.feedback

@pytest.mark.asyncio
async def test_malformed_llm_output(agent):
    plan = create_valid_project_plan()
    agent.llm.exceptions = [ValidationError.from_exception_data("error", line_errors=[])]
    agent.llm.responses = [plan]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 2

@pytest.mark.asyncio
async def test_llm_failure(agent):
    agent.llm.exceptions = [LLMException("Timeout")]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.FAILURE
    assert "Timeout" in out.feedback

@pytest.mark.asyncio
async def test_rag_success():
    llm = MockLLMClient()
    llm.responses = [create_valid_project_plan()]
    rag = MockRAGService(context=KnowledgeContext(query="test", chunks=[KnowledgeChunk(content="Domain knowledge", similarity_score=0.9, source="test")]))
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "Domain knowledge" in llm.captured_prompts[0]

@pytest.mark.asyncio
async def test_rag_failure():
    llm = MockLLMClient()
    llm.responses = [create_valid_project_plan()]
    rag = MockRAGService(should_fail=True)
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS # Graceful degradation
    assert rag.call_count == 1

@pytest.mark.asyncio
async def test_empty_rag_context():
    llm = MockLLMClient()
    llm.responses = [create_valid_project_plan()]
    rag = MockRAGService(context=KnowledgeContext(query="test", chunks=[]))
    agent = PlanningAgent(llm_client=llm, rag_service=rag)
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "RETRIEVED DOMAIN KNOWLEDGE" not in llm.captured_prompts[0]

@pytest.mark.asyncio
async def test_projectplan_validation(agent):
    # Testing that it returns valid structure
    agent.llm.responses = [create_valid_project_plan()]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert "architecture_summary" in out.result

@pytest.mark.asyncio
async def test_acceptance_criteria_generation(agent):
    agent.llm.responses = [create_valid_project_plan()]
    out = await agent.execute(create_input({"project_id": "p-1"}))
    assert out.status == AgentStatus.SUCCESS
    assert out.result["tasks"][0]["input_data"]["acceptance_criteria"] == "Tests pass"
