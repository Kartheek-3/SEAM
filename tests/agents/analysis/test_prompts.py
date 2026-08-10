"""
Tests for Analysis Agent prompt formatting.
"""

from agents.analysis.prompts import USER_PROMPT_TEMPLATE, REWORK_SECTION_TEMPLATE

def test_user_prompt_formatting():
    prompt = USER_PROMPT_TEMPLATE.format(
        raw_description="Build a CRM.",
        knowledge_section="",
        instructions="Extract everything.",
        rework_section=""
    )
    assert "Build a CRM." in prompt
    assert "Extract everything." in prompt
    assert "URGENT REWORK FEEDBACK" not in prompt

def test_knowledge_section_formatting():
    from agents.analysis.prompts import KNOWLEDGE_SECTION_TEMPLATE
    knowledge = KNOWLEDGE_SECTION_TEMPLATE.format(knowledge_text="Past CRM patterns: Use PostgreSQL.")
    assert "Past CRM patterns: Use PostgreSQL." in knowledge
    assert "RETRIEVED DOMAIN KNOWLEDGE" in knowledge

def test_rework_section_formatting():
    rework = REWORK_SECTION_TEMPLATE.format(
        rework_instructions="Fix domain entities.",
        focus_areas="User, Account",
        qa_findings="- [MAJOR] Missing user entity"
    )
    assert "Fix domain entities." in rework
    assert "User, Account" in rework
    assert "[MAJOR] Missing user entity" in rework
