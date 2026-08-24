import pytest
from agents.delivery.agent import DeliveryAgent, DeliveryQAGateError
from backend.schemas import AgentInput, TaskType
from unittest.mock import MagicMock

def test_delivery_gate_success():
    agent = DeliveryAgent(llm_client=MagicMock())
    input_data = AgentInput(
        task_id="delivery",
        task_type=TaskType.DELIVERY,
        instructions="deliver",
        dependencies=["qa-1", "qa-2"],
        context={
            "qa_results": [
                {"task_id": "qa-1", "verdict": "pass"},
                {"task_id": "qa-2", "verdict": "pass"}
            ]
        }
    )
    # Should not raise
    agent._validate_qa_gate(input_data)

def test_delivery_gate_missing_qa():
    agent = DeliveryAgent(llm_client=MagicMock())
    input_data = AgentInput(
        task_id="delivery",
        task_type=TaskType.DELIVERY,
        instructions="deliver",
        dependencies=["qa-1", "qa-2"],
        context={
            "qa_results": [
                {"task_id": "qa-1", "verdict": "pass"}
                # Missing qa-2
            ]
        }
    )
    with pytest.raises(DeliveryQAGateError, match="Mismatched QA tasks"):
        agent._validate_qa_gate(input_data)

def test_delivery_gate_fail_verdict():
    agent = DeliveryAgent(llm_client=MagicMock())
    input_data = AgentInput(
        task_id="delivery",
        task_type=TaskType.DELIVERY,
        instructions="deliver",
        dependencies=["qa-1"],
        context={
            "qa_results": [
                {"task_id": "qa-1", "verdict": "fail"}
            ]
        }
    )
    with pytest.raises(DeliveryQAGateError, match="QA verdict is fail"):
        agent._validate_qa_gate(input_data)
