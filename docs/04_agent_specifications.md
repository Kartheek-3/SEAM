# 04 — Agent Specifications

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Agent Overview

SEAM comprises exactly **six** executable agents. Each agent is a specialised
module responsible for one phase of the software-engineering lifecycle.

| # | Agent | Responsibility | Primary LLM |
|---|-------|---------------|-------------|
| 1 | Analysis Agent | Requirements extraction and domain analysis | Llama 3.1 |
| 2 | Planning & Design Agent | Architecture design and task decomposition | Llama 3.1 |
| 3 | Supervisor/Orchestrator | Dynamic task coordination and quality gating | Llama 3.1 |
| 4 | Coding Agent | Code generation and modification | DeepSeek-Coder |
| 5 | QA Agent | Testing, code review, and quality assessment | DeepSeek-Coder |
| 6 | Delivery Agent | Packaging, documentation, and deployment preparation | Llama 3.1 |

## 2. Common Agent Interface

All agents inherit from `BaseAgent` and implement:

```python
class BaseAgent(ABC):
    """Abstract base class for all SEAM agents."""

    def __init__(self, agent_id: str, config: AgentConfig, rag_service: RAGService):
        ...

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's primary task."""
        ...

    async def query_knowledge(self, query: str) -> list[Document]:
        """Retrieve relevant context via the shared RAG service."""
        ...
```

### Common Input/Output Models

```python
class AgentInput(BaseModel):
    task_id: str
    task_type: str
    context: dict[str, Any]
    instructions: str
    dependencies: list[str] = []
    rework_feedback: ReworkFeedback | None = None
    metadata: dict[str, Any] = {}

class AgentOutput(BaseModel):
    task_id: str
    agent_id: str
    status: Literal["success", "partial", "failure"]
    result: dict[str, Any]
    artifacts: list[Artifact] = []
    confidence: float = 0.0
    feedback: str = ""
    metadata: dict[str, Any] = {}
```

---

## 3. Agent Specifications

### 3.1 Analysis Agent

**Purpose:** Extract, clarify, and structure software requirements from
natural-language project descriptions.

**Inputs:**
- Raw project description (natural language)
- Domain context from knowledge repository

**Outputs:**
- Structured requirements document (functional & non-functional)
- Identified ambiguities and assumptions
- Domain entities and relationships

**Key Behaviours:**
- Queries the shared RAG infrastructure to obtain relevant domain knowledge before LLM-based analysis
- Identifies missing information and flags ambiguities
- Produces structured output suitable for the Planning & Design Agent

**LLM:** Llama 3.1 (strong instruction following and reasoning)

---

### 3.2 Planning & Design Agent

**Purpose:** Produce an architectural design and decompose the project into
implementable tasks.

**Inputs:**
- Structured requirements from the Analysis Agent
- Technology constraints and preferences
- Past architectural patterns from knowledge repository

**Outputs:**
- System architecture document
- Component breakdown
- Task list with dependencies and priorities
- Technology recommendations

**Key Behaviours:**
- Leverages past designs from the knowledge repository
- Produces a task dependency graph
- Estimates complexity for each task

**LLM:** Llama 3.1

---

### 3.3 Supervisor/Orchestrator Agent

**Purpose:** Coordinate all other agents dynamically. Assign tasks, evaluate
intermediate results, enforce quality gates, and trigger rework.

**Inputs:**
- Task dependency graph from the Planning & Design Agent
- Intermediate results from other agents
- QA reports

**Outputs:**
- Task assignments with routing decisions
- Evaluation verdicts (pass / rework / escalate)
- Workflow state updates

**Key Behaviours:**
- Maintains a LangGraph state machine
- Does NOT follow a static sequential pipeline
- Evaluates agent outputs against quality criteria
- Triggers rework cycles when QA reports failures
- Tracks overall project progress and dependencies

**LLM:** Llama 3.1 (for evaluation and decision-making)

*See [05_supervisor_algorithm.md](05_supervisor_algorithm.md) for detailed
orchestration logic.*

---

### 3.4 Coding Agent

**Purpose:** Generate, modify, and refactor source code based on task
specifications.

**Inputs:**
- Task specification from the Supervisor
- Relevant code context from RAG
- Architecture constraints from the Planning Agent

**Outputs:**
- Generated source code files
- Inline documentation and comments
- Change summary

**Key Behaviours:**
- Uses DeepSeek-Coder for high-quality code generation
- Queries RAG for existing code patterns and conventions
- Respects architectural constraints
- Produces code that includes basic documentation

**LLM:** DeepSeek-Coder (specialised for code generation)

---

### 3.5 QA Agent

**Purpose:** Validate the quality of generated code and artifacts through
automated testing, code review, and quality assessment.

**Inputs:**
- Generated code from the Coding Agent
- Requirements from the Analysis Agent
- Architecture from the Planning Agent

**Outputs:**
- Test results (pass/fail with details)
- Code review findings
- Quality score and metrics
- Rework recommendations (if quality is insufficient)

**Key Behaviours:**
- Generates and runs unit tests
- Performs static analysis and code review
- Compares output against requirements
- Provides actionable rework feedback to the Supervisor/Orchestrator
- Reports quality verdicts to the Supervisor

**LLM:** DeepSeek-Coder (understands code well enough to test and review it)

---

### 3.6 Delivery Agent

**Purpose:** Prepare the final deliverables: package code, generate
documentation, create deployment configurations.

**Inputs:**
- Validated code from the Coding Agent (post-QA)
- Project requirements and architecture documents

**Outputs:**
- Packaged application
- Generated user documentation
- Deployment configurations (Dockerfiles, compose files)
- Release notes

**Key Behaviours:**
- Only invoked after QA approval
- Generates deployment artifacts
- Produces human-readable documentation
- Creates a final project summary

**LLM:** Llama 3.1

---

## 4. Agent Interaction Matrix

| From ↓ / To → | Analysis | Planning | Supervisor | Coding | QA | Delivery |
|----------------|----------|----------|-----------|--------|-----|---------|
| **Analysis** | — | Output feeds | Reports to | — | — | — |
| **Planning** | — | — | Reports to | — | — | — |
| **Supervisor** | Dispatches | Dispatches | — | Dispatches | Dispatches | Dispatches |
| **Coding** | — | — | Reports to | — | — | — |
| **QA** | — | — | Reports to | Feedback (via Supervisor) | — | — |
| **Delivery** | — | — | Reports to | — | — | — |

> **Note:** All inter-agent communication is mediated by the
> Supervisor/Orchestrator. Agents do not communicate directly with each
> other. When the QA Agent identifies quality issues, it reports its
> findings to the Supervisor, which then dispatches structured rework instructions
> (including QA feedback via the `ReworkFeedback` schema) to the Coding Agent via the `rework_feedback`
> field in `AgentInput`.
>
> ```
> QA Agent → Supervisor/Orchestrator → Coding Agent
> ```
