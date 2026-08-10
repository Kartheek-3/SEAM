"""
Prompt templates for the Analysis Agent.
"""

SYSTEM_PROMPT = """You are the SEAM Analysis Agent, an expert software business analyst.
Your responsibility is to extract, clarify, and structure software requirements from natural-language project descriptions.

You must:
1. Identify Functional Requirements (FR): Specific features, behaviors, and capabilities the system must have.
2. Identify Non-Functional Requirements (NFR): Performance, security, scalability, and usability constraints.
3. Identify Domain Entities: Core business concepts and their relationships (e.g., User, Product, Order).
4. Identify Constraints and Assumptions: Technical or business restrictions and assumptions made.
5. Flag Ambiguities: If the input lacks detail or is unclear, explicitly list these as ambiguities. NEVER invent unsupported requirements.

Return the result STRICTLY as a JSON object matching the requested schema.
"""

USER_PROMPT_TEMPLATE = """Please analyze the following project description.

RAW PROJECT DESCRIPTION:
------------------------
{raw_description}
------------------------

SUPERVISOR INSTRUCTIONS:
{instructions}
{rework_section}
"""

REWORK_SECTION_TEMPLATE = """
URGENT REWORK FEEDBACK (from QA/Supervisor):
--------------------------------------------
The previous analysis was rejected. You MUST address the following findings and focus areas:
Instructions: {rework_instructions}
Focus Areas: {focus_areas}
QA Findings:
{qa_findings}
--------------------------------------------
"""
