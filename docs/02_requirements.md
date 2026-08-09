# 02 — Requirements

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Functional Requirements

### FR-1: Agent Execution

| ID | Requirement |
|----|-------------|
| FR-1.1 | The system SHALL provide six executable agents: Analysis, Planning & Design, Supervisor/Orchestrator, Coding, QA, and Delivery |
| FR-1.2 | Each agent SHALL expose a consistent invocation interface |
| FR-1.3 | Each agent SHALL accept structured input and produce structured output |
| FR-1.4 | Each agent SHALL be able to query the shared RAG infrastructure |
| FR-1.5 | Each agent SHALL log its actions and decisions for traceability |

### FR-2: Supervisor/Orchestrator

| ID | Requirement |
|----|-------------|
| FR-2.1 | The Supervisor SHALL dynamically assign tasks to agents based on project state |
| FR-2.2 | The Supervisor SHALL check dependencies before dispatching tasks |
| FR-2.3 | The Supervisor SHALL evaluate intermediate results from agents |
| FR-2.4 | The Supervisor SHALL trigger rework cycles when QA reports failures |
| FR-2.5 | The Supervisor SHALL maintain a state machine tracking overall workflow progress |
| FR-2.6 | The Supervisor SHALL NOT use a static sequential pipeline |

### FR-3: RAG Infrastructure

| ID | Requirement |
|----|-------------|
| FR-3.1 | The RAG subsystem SHALL be implemented as shared infrastructure, not as an agent |
| FR-3.2 | The RAG subsystem SHALL chunk, embed, and index documents into ChromaDB |
| FR-3.3 | The RAG subsystem SHALL support similarity-based retrieval with configurable top-k |
| FR-3.4 | The RAG subsystem SHALL be accessible to all six agents |

### FR-4: Knowledge Repository

| ID | Requirement |
|----|-------------|
| FR-4.1 | The system SHALL persist validated knowledge from completed tasks |
| FR-4.2 | The system SHALL retrieve relevant past knowledge during new task execution |
| FR-4.3 | Continuous learning SHALL be achieved via stored knowledge, NOT by retraining the LLM |
| FR-4.4 | The knowledge repository SHALL support versioning of knowledge entries |

### FR-5: User Interface

| ID | Requirement |
|----|-------------|
| FR-5.1 | The frontend SHALL provide a dashboard for initiating projects |
| FR-5.2 | The frontend SHALL display real-time agent activity and status |
| FR-5.3 | The frontend SHALL allow users to view generated artifacts (code, docs, tests) |
| FR-5.4 | The frontend SHALL provide a way to inspect the orchestration state |

### FR-6: Backend API

| ID | Requirement |
|----|-------------|
| FR-6.1 | The backend SHALL expose RESTful endpoints for project management |
| FR-6.2 | The backend SHALL support WebSocket connections for real-time status updates |
| FR-6.3 | The backend SHALL validate all inputs using Pydantic models |

## 2. Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement |
|----|-------------|
| NFR-1.1 | Agent response time SHALL be bounded by the underlying LLM inference time plus 2 seconds overhead |
| NFR-1.2 | RAG retrieval SHALL complete within 1 second for collections under 10,000 documents |

### NFR-2: Modularity

| ID | Requirement |
|----|-------------|
| NFR-2.1 | Each agent SHALL be independently deployable and testable |
| NFR-2.2 | The RAG infrastructure SHALL be decoupled from agent implementations |
| NFR-2.3 | The orchestration logic SHALL be separated from agent business logic |

### NFR-3: Extensibility

| ID | Requirement |
|----|-------------|
| NFR-3.1 | Adding a new LLM model SHALL require only configuration changes |
| NFR-3.2 | Prompt templates SHALL be externalized and version-controlled |

### NFR-4: Reliability

| ID | Requirement |
|----|-------------|
| NFR-4.1 | The system SHALL handle LLM timeout errors gracefully with retry logic |
| NFR-4.2 | Agent failures SHALL not crash the Supervisor; they SHALL be reported and recoverable |

### NFR-5: Observability

| ID | Requirement |
|----|-------------|
| NFR-5.1 | All agent invocations SHALL be logged with timestamps and trace IDs |
| NFR-5.2 | The system SHALL expose health-check endpoints |

### NFR-6: Reproducibility

| ID | Requirement |
|----|-------------|
| NFR-6.1 | Experiments SHALL be reproducible given the same inputs and model versions |
| NFR-6.2 | All configurations SHALL be captured in version-controlled files |

## 3. Constraints

| Constraint | Description |
|-----------|-------------|
| C1 | Must use Ollama for local LLM inference (no cloud API dependencies) |
| C2 | Must use ChromaDB as the vector store |
| C3 | Must limit to exactly six agents (no additional agents) |
| C4 | Must be completable within the final-year project timeline |

## 4. Assumptions

| Assumption | Description |
|-----------|-------------|
| A1 | Ollama can run DeepSeek-Coder and Llama 3.1 on the development machine |
| A2 | The development machine has sufficient GPU/CPU resources for local inference |
| A3 | Python 3.11+ is available on the target platform |
| A4 | The project will primarily target single-user, single-project execution |

## 5. Traceability Matrix

*To be populated as implementation progresses. Each requirement ID will be
mapped to its implementing module, test case, and verification status.*
