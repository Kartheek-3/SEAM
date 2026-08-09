# 13 — Testing

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Overview

SEAM uses a multi-layered testing strategy to ensure correctness, reliability,
and quality at every level of the system.

## 2. Testing Pyramid

```
        ┌──────────┐
        │   E2E    │  Few, high-value end-to-end tests
        ├──────────┤
        │ Integr.  │  Component interaction tests
        ├──────────┤
        │  Unit    │  Comprehensive unit tests
        └──────────┘
```

## 3. Test Categories

### 3.1 Unit Tests

**Scope:** Individual functions, classes, and methods in isolation.

| Component | Test Focus |
|-----------|-----------|
| Agents | Agent input parsing, output formatting, prompt building |
| RAG | Chunking strategies, embedding calls, retriever logic |
| Knowledge | CRUD operations, validation logic |
| Orchestration | State transitions, decision logic |
| Backend | API endpoint handlers, Pydantic model validation |

**Tools:** `pytest`, `pytest-asyncio`

### 3.2 Integration Tests

**Scope:** Interaction between components.

| Integration Point | Test Focus |
|-------------------|-----------|
| Agent → RAG | Agent correctly queries and uses RAG context |
| Supervisor → Agent | Task dispatch and result collection |
| API → Orchestration | REST endpoint triggers orchestration correctly |
| RAG → ChromaDB | Document ingestion and retrieval accuracy |

**Tools:** `pytest`, `httpx` (for async API testing)

### 3.3 End-to-End Tests

**Scope:** Full workflow from user input to final output.

| Scenario | Description |
|----------|-------------|
| Happy path | Project submitted → Analysis → Planning → Coding → QA → Delivery |
| Rework cycle | QA failure triggers rework, resolved on retry |
| Error recovery | Agent timeout is handled gracefully by Supervisor |

**Tools:** `pytest`, potentially with `requests` for API-level E2E

## 4. Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py               # Shared fixtures
├── unit/
│   ├── test_agents/
│   ├── test_rag/
│   ├── test_knowledge/
│   ├── test_orchestration/
│   └── test_backend/
├── integration/
│   ├── test_agent_rag.py
│   ├── test_supervisor_agents.py
│   └── test_api_orchestration.py
└── e2e/
    ├── test_happy_path.py
    └── test_rework_cycle.py
```

## 5. Test Configuration

**`pyproject.toml` or `pytest.ini`:**
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Tests that take > 10s"
]
```

## 6. Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Agents | ≥ 80% |
| RAG | ≥ 85% |
| Knowledge | ≥ 85% |
| Orchestration | ≥ 90% |
| Backend API | ≥ 80% |

**Tools:** `pytest-cov`

## 7. Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# With coverage report
pytest --cov=. --cov-report=html

# Specific component
pytest tests/unit/test_agents/
```

## 8. Continuous Integration

*To be configured in later phases. Tests will run on every push via
GitHub Actions or similar CI.*
