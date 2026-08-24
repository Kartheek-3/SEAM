"""
End-to-End Integration Tests for SEAM Framework.

This suite instantiates the full Six-Agent architecture and verifies that
they interoperate flawlessly through the Supervisor state machine.
The LLM responses are mocked to simulate realistic outputs and workflow variations.
"""

import pytest
import os
from datetime import datetime, timezone
from typing import Any

from backend.schemas.agent_io import AgentInput, AgentOutput, AgentStatus, AgentRole
from backend.schemas.enums import TaskType, QAVerdict, FindingSeverity, ArtifactType
from backend.schemas.analysis import RequirementSpec, RequirementItem
from backend.schemas.planning import ProjectPlan, Task
from backend.schemas.qa import QAResult, QAFinding
from backend.schemas.artifacts import Artifact
from agents.coding.agent import CodeGenerationResponse, GeneratedFile as CodingGeneratedFile
from agents.delivery.agent import DeliveryGenerationResponse, GeneratedFile as DeliveryGeneratedFile

from agents.analysis.agent import AnalysisAgent
from agents.planning.agent import PlanningAgent
from agents.coding.agent import CodingAgent
from agents.qa.agent import QAAgent
from agents.delivery.agent import DeliveryAgent
from agents.supervisor.agent import SupervisorAgent

now = datetime.now(timezone.utc)

class SmartMockLLM:
    """
    An LLM Mock that returns predefined valid schemas based on the requested model type.
    It can be configured to fail QA on specific attempts to simulate rework.
    """
    def __init__(self, qa_failures: int = 0):
        self.call_count = 0
        self.qa_failures = qa_failures
        self.qa_attempts = 0

    async def generate_structured_response(self, system_prompt: str, user_prompt: str, response_model: type) -> Any:
        return await self._generate(response_model)
        
    async def generate_structured_output(self, system_prompt: str, user_prompt: str, response_model: type) -> Any:
        return await self._generate(response_model)

    async def _generate(self, response_model: type) -> Any:
        self.call_count += 1
        model_name = response_model.__name__

        if model_name == "RequirementSpec":
            return RequirementSpec(
                project_id="req-1",
                functional_requirements=[RequirementItem(id="fr-1", description="User auth", category="functional", priority="must")],
                non_functional_requirements=[],
                ambiguities=[],
                assumptions=[],
                domain_entities=[]
            )
        
        elif model_name == "ProjectPlan":
            return ProjectPlan(
                project_id="req-1",
                architecture_summary="3-tier architecture",
                components=[],
                tasks=[
                    Task(id="T-1", project_id="req-1", title="Backend Setup", description="Setup FastAPI", type=TaskType.CODING, dependencies=[]),
                    Task(id="T-2", project_id="req-1", title="Backend QA", description="QA Backend", type=TaskType.QA, dependencies=["T-1"]),
                    Task(id="T-3", project_id="req-1", title="Delivery", description="Package app", type=TaskType.DELIVERY, dependencies=["T-2"])
                ]
            )
            
        elif model_name == "CodeGenerationResponse":
            return CodeGenerationResponse(
                files=[
                    CodingGeneratedFile(path="src/main.py", content="print('hello')", language="python", artifact_type=ArtifactType.CODE)
                ]
            )
            
        elif model_name == "QAEvaluationResponse":
            from agents.qa.agent import QAEvaluationResponse
            self.qa_attempts += 1
            if self.qa_attempts <= self.qa_failures:
                return QAEvaluationResponse(
                    findings=[QAFinding(category="code_review", description="Missing tests", severity=FindingSeverity.CRITICAL, file_path="src/main.py")],
                    tests_passed=0,
                    tests_failed=1,
                    tests_total=1,
                    recommendations=[]
                )
            else:
                return QAEvaluationResponse(
                    findings=[],
                    tests_passed=1,
                    tests_failed=0,
                    tests_total=1,
                    recommendations=[]
                )
                
        elif model_name == "DeliveryGenerationResponse":
            return DeliveryGenerationResponse(
                files=[
                    DeliveryGeneratedFile(path="Dockerfile", content="FROM python:3.11", language="dockerfile")
                ],
                metadata={}
            )
            
        raise ValueError(f"MockLLM does not know how to generate {model_name}")

@pytest.fixture
def supervisor():
    mock_llm = SmartMockLLM(qa_failures=0)
    
    # Construct all 6 agents (pass mock_llm where required, or inject later)
    analysis = AnalysisAgent(llm_client=mock_llm)
    planning = PlanningAgent(llm_client=mock_llm)
    coding = CodingAgent(llm_client=mock_llm)
    qa = QAAgent(llm_client=mock_llm)
    delivery = DeliveryAgent(llm_client=mock_llm)
    
    # Initialize the registry
    registry = {
        TaskType.ANALYSIS: analysis,
        TaskType.PLANNING: planning,
        TaskType.CODING: coding,
        TaskType.QA: qa,
        TaskType.DELIVERY: delivery
    }
    
    sup = SupervisorAgent(agent_registry=registry)
    return sup

@pytest.mark.asyncio
async def test_e2e_successful_workflow(supervisor):
    """
    Simulates a perfect run: Analysis -> Planning -> Coding -> QA (PASS) -> Delivery.
    """
    # Inject standard mocks that don't fail
    for agent in supervisor.agent_registry.values():
        agent.llm = SmartMockLLM(qa_failures=0)
        
    # We simulate starting from the Supervisor with the ProjectPlan already created by Planning.
    # In a full run, we just need to provide the ProjectPlan to the Supervisor.
    plan = ProjectPlan(
        project_id="proj-1",
        architecture_summary="Test",
        components=[],
        tasks=[
            Task(id="T-1", project_id="proj-1", title="Code", description="Code", type=TaskType.CODING, dependencies=[], created_at=now),
            Task(id="T-2", project_id="proj-1", title="QA", description="QA", type=TaskType.QA, dependencies=["T-1"], created_at=now),
            Task(id="T-3", project_id="proj-1", title="Del", description="Del", type=TaskType.DELIVERY, dependencies=["T-1", "T-2"], created_at=now)
        ]
    )
    
    inp = AgentInput(
        task_id="sup-main",
        task_type=TaskType.PLANNING,
        context={"project_plan": plan.model_dump()},
        instructions="Run"
    )
    
    out = await supervisor.execute(inp)
    assert out.status == AgentStatus.SUCCESS
    
    # Verify final artifacts are aggregated properly
    final_artifacts = out.artifacts
    # T-1 code artifact is collected multiple times (direct dep + QA traversal from T-3),
    # plus the Dockerfile from Delivery (T-3). Exact count: 4
    assert len(final_artifacts) == 4
    names = [a.name for a in final_artifacts]
    assert "src/main.py" in names
    assert "Dockerfile" in names

@pytest.mark.asyncio
async def test_e2e_adaptive_rework_workflow(supervisor):
    """
    Simulates a QA failure followed by a successful retry.
    Workflow: Coding -> QA (FAIL) -> Supervisor increments rework -> Coding -> QA (PASS) -> Delivery.
    """
    for agent in supervisor.agent_registry.values():
        agent.llm = SmartMockLLM(qa_failures=1)
        
    plan = ProjectPlan(
        project_id="proj-1",
        architecture_summary="Test",
        components=[],
        tasks=[
            Task(id="T-1", project_id="proj-1", title="Code", description="Code", type=TaskType.CODING, dependencies=[], created_at=now),
            Task(id="T-2", project_id="proj-1", title="QA", description="QA", type=TaskType.QA, dependencies=["T-1"], created_at=now),
            Task(id="T-3", project_id="proj-1", title="Del", description="Del", type=TaskType.DELIVERY, dependencies=["T-1", "T-2"], created_at=now)
        ]
    )
    
    inp = AgentInput(
        task_id="sup-main",
        task_type=TaskType.PLANNING,
        context={"project_plan": plan.model_dump()},
        instructions="Run"
    )
    
    out = await supervisor.execute(inp)
    assert out.status == AgentStatus.SUCCESS
    
    # Check rework counter was hit
    assert out.result["rework_counts"]["T-1"] == 1
    
    # Coding agent should have been called twice
    assert supervisor.agent_registry[TaskType.CODING].llm.call_count == 2
    # QA agent should have been called twice
    assert supervisor.agent_registry[TaskType.QA].llm.call_count == 2
    # Delivery agent should have been called once
    assert supervisor.agent_registry[TaskType.DELIVERY].llm.call_count == 1

@pytest.mark.asyncio
async def test_e2e_qa_max_retries(supervisor):
    """
    Simulates a QA failure that exceeds max retries.
    Workflow: Coding -> QA (FAIL) -> Supervisor loops until max rework limit -> Pipeline terminates.
    """
    for agent in supervisor.agent_registry.values():
        # Force QA to always fail (more than 3 times)
        agent.llm = SmartMockLLM(qa_failures=5)
        
    plan = ProjectPlan(
        project_id="proj-1",
        architecture_summary="Test",
        components=[],
        tasks=[
            Task(id="T-1", project_id="proj-1", title="Code", description="Code", type=TaskType.CODING, dependencies=[], created_at=now),
            Task(id="T-2", project_id="proj-1", title="QA", description="QA", type=TaskType.QA, dependencies=["T-1"], created_at=now),
            Task(id="T-3", project_id="proj-1", title="Del", description="Del", type=TaskType.DELIVERY, dependencies=["T-1", "T-2"], created_at=now)
        ]
    )
    
    inp = AgentInput(
        task_id="sup-main",
        task_type=TaskType.PLANNING,
        context={"project_plan": plan.model_dump()},
        instructions="Run"
    )
    
    out = await supervisor.execute(inp)
    # The supervisor should eventually give up and fail
    assert out.status == AgentStatus.FAILURE
    
    # The supervisor returns the state when it fails
    assert "T-1" in out.result["failed_tasks"]
    assert out.result["rework_counts"]["T-1"] >= 3
    
    # Delivery agent should NEVER be called because QA blocked it
    assert supervisor.agent_registry[TaskType.DELIVERY].llm.call_count == 0
