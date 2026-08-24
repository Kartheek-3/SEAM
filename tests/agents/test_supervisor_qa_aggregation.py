import pytest
import time
from datetime import datetime, timezone
from agents.supervisor.agent import SupervisorAgent
from backend.schemas import TaskType, Task, AgentInput, AgentOutput, AgentStatus, AgentRole
from backend.schemas.workflow import WorkflowState
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_registry():
    mock_qa = AsyncMock()
    mock_qa.execute.return_value = AgentOutput(
        task_id="qa-1", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "pass", "task_id": "qa-1"}
    )
    return {
        TaskType.QA: mock_qa,
        TaskType.CODING: AsyncMock(),
        TaskType.DELIVERY: AsyncMock(),
    }

@pytest.mark.asyncio
async def test_single_qa_result_propagation(mock_registry):
    supervisor = SupervisorAgent(agent_registry=mock_registry)
    now = datetime.now(timezone.utc)
    
    # Simulate a state where a Delivery task depends on a single QA task
    state: WorkflowState = {
        "project_id": "test",
        "current_phase": "test",
        "tasks": {
            "qa-1": Task(id="qa-1", project_id="test", title="QA 1", description="desc", created_at=now, type=TaskType.QA),
            "del-1": Task(id="del-1", project_id="test", title="Del 1", description="desc", created_at=now, type=TaskType.DELIVERY, dependencies=["qa-1"])
        },
        "pending_tasks": [],
        "running_tasks": [],
        "completed_tasks": ["qa-1"],
        "failed_tasks": [],
        "agent_outputs": {
            "qa-1": AgentOutput(task_id="qa-1", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "pass", "task_id": "qa-1"})
        },
        "rework_counts": {},
        "quality_scores": {},
        "current_task_id": "del-1",
        "messages": [],
        "final_artifacts": [],
        "qa_execution_history": []
    }
    
    # We run _node_agent_execution to see how context is built for del-1
    mock_del = mock_registry[TaskType.DELIVERY]
    await supervisor._node_agent_execution(state)
    
    # Check what was passed to Delivery
    call_args = mock_del.execute.call_args[0][0]
    assert call_args.task_id == "del-1"
    
    context = call_args.context
    assert "qa_result" in context
    assert "qa_results" in context
    assert len(context["qa_results"]) == 1
    assert context["qa_results"][0]["task_id"] == "qa-1"

@pytest.mark.asyncio
async def test_multiple_qa_results_propagation(mock_registry):
    supervisor = SupervisorAgent(agent_registry=mock_registry)
    now = datetime.now(timezone.utc)
    
    # Simulate a state where a Delivery task depends on MULTIPLE QA tasks
    state: WorkflowState = {
        "project_id": "test",
        "current_phase": "test",
        "tasks": {
            "qa-1": Task(id="qa-1", project_id="test", title="QA 1", description="desc", created_at=now, type=TaskType.QA),
            "qa-2": Task(id="qa-2", project_id="test", title="QA 2", description="desc", created_at=now, type=TaskType.QA),
            "del-1": Task(id="del-1", project_id="test", title="Del 1", description="desc", created_at=now, type=TaskType.DELIVERY, dependencies=["qa-1", "qa-2"])
        },
        "pending_tasks": [],
        "running_tasks": [],
        "completed_tasks": ["qa-1", "qa-2"],
        "failed_tasks": [],
        "agent_outputs": {
            "qa-1": AgentOutput(task_id="qa-1", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "pass", "task_id": "qa-1"}),
            "qa-2": AgentOutput(task_id="qa-2", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "pass", "task_id": "qa-2"})
        },
        "rework_counts": {},
        "quality_scores": {},
        "current_task_id": "del-1",
        "messages": [],
        "final_artifacts": [],
        "qa_execution_history": []
    }
    
    mock_del = mock_registry[TaskType.DELIVERY]
    await supervisor._node_agent_execution(state)
    
    call_args = mock_del.execute.call_args[0][0]
    context = call_args.context
    assert "qa_results" in context
    assert len(context["qa_results"]) == 2
    task_ids = [r["task_id"] for r in context["qa_results"]]
    assert "qa-1" in task_ids
    assert "qa-2" in task_ids

@pytest.mark.asyncio
async def test_rework_history_preserved(mock_registry):
    supervisor = SupervisorAgent(agent_registry=mock_registry)
    now = datetime.now(timezone.utc)
    
    state: WorkflowState = {
        "project_id": "test",
        "current_phase": "test",
        "tasks": {
            "qa-1": Task(id="qa-1", project_id="test", title="QA 1", description="desc", created_at=now, type=TaskType.QA)
        },
        "pending_tasks": [],
        "running_tasks": ["qa-1"],
        "completed_tasks": [],
        "failed_tasks": [],
        "agent_outputs": {
            # Initial state before eval output
            "qa-1": AgentOutput(task_id="qa-1", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "fail", "task_id": "qa-1"})
        },
        "rework_counts": {},
        "quality_scores": {},
        "current_task_id": "qa-1",
        "messages": [],
        "final_artifacts": [],
        "qa_execution_history": []
    }
    
    # Simulating first eval (FAIL)
    await supervisor._node_eval_output(state)
    assert len(state["qa_execution_history"]) == 1
    assert state["qa_execution_history"][0]["verdict"] == "fail"
    
    # Rework happens...
    state["running_tasks"] = ["qa-1"]
    state["current_task_id"] = "qa-1"
    state["rework_counts"]["qa-1"] = 1
    # New agent output (PASS)
    state["agent_outputs"]["qa-1"] = AgentOutput(task_id="qa-1", agent_id=AgentRole.QA, status=AgentStatus.SUCCESS, result={"verdict": "pass", "task_id": "qa-1"})
    
    # Simulating second eval (PASS)
    await supervisor._node_eval_output(state)
    assert len(state["qa_execution_history"]) == 2
    assert state["qa_execution_history"][0]["verdict"] == "fail"
    assert state["qa_execution_history"][1]["verdict"] == "pass"
    assert state["qa_execution_history"][1]["attempt"] == 2
