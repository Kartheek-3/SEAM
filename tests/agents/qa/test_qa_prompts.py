import pytest
from agents.qa.prompts import SYSTEM_PROMPT

def test_qa_system_prompt_demands_object():
    """
    Ensures that the QA system prompt explicitly requests a complete QA evaluation response
    object, and DOES NOT instruct the model to return a root list.
    """
    assert "response object" in SYSTEM_PROMPT.lower(), "System prompt must request an object."
    assert "list of structured findings. if the code perfectly matches" not in SYSTEM_PROMPT, "System prompt must not instruct the model to return a root list."
    assert "inside the object" in SYSTEM_PROMPT.lower(), "System prompt should clarify the findings list goes inside the object."
