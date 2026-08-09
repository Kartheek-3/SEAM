# 01 — Project Charter

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Project Title

**SEAM** — Self-Evolving Autonomous Multi-Agent Framework

## 2. Project Summary

SEAM is a final-year research project that designs, implements, and evaluates
a domain-aware, adaptive multi-agent framework for end-to-end software
engineering. The framework uses six specialised AI agents coordinated by a
Supervisor/Orchestrator to autonomously perform requirements analysis,
architecture design, code generation, quality assurance, and delivery.

## 3. Problem Statement

Modern software engineering increasingly leverages LLM-based tools, but most
existing solutions either:

- Operate as single-agent systems (e.g., code completion tools) with limited
  scope,
- Use static, sequential pipelines that cannot adapt to task complexity, or
- Lack mechanisms for continuous learning from past project outcomes.

There is a need for a **multi-agent framework** that can dynamically coordinate
specialised agents, leverage domain knowledge, and improve over time without
retraining the underlying LLMs.

## 4. Objectives

| ID | Objective |
|----|-----------|
| O1 | Design a six-agent architecture that covers the full software-engineering lifecycle |
| O2 | Implement a Supervisor/Orchestrator with dynamic task assignment and QA-driven rework |
| O3 | Build a shared RAG infrastructure backed by ChromaDB for context retrieval |
| O4 | Implement continuous learning through a persistent Organizational Knowledge Repository |
| O5 | Evaluate the framework against baseline approaches using defined metrics |
| O6 | Deploy the system with Docker for reproducible experimentation |

## 5. Scope

### In Scope

- Six executable agents: Analysis, Planning & Design, Supervisor/Orchestrator,
  Coding, QA, Delivery
- Shared RAG infrastructure (not an independent agent)
- ChromaDB vector store
- Organizational Knowledge Repository for continuous learning
- FastAPI backend, React + Vite frontend
- Local LLM inference via Ollama (DeepSeek-Coder, Llama 3.1)
- Docker-based deployment
- Evaluation experiments and documented results

### Out of Scope

- Production-grade security hardening (this is a research prototype)
- LLM fine-tuning or retraining
- Support for cloud-hosted LLM providers (Ollama-only for now)
- Additional agents beyond the defined six

## 6. Stakeholders

| Role | Responsibility |
|------|---------------|
| Student Researcher | Design, implementation, testing, evaluation, and documentation |
| Project Supervisor | Academic guidance, milestone review, and grading |
| Examiners | Final evaluation of the submitted dissertation and prototype |

## 7. Deliverables

| Deliverable | Description |
|-------------|-------------|
| Source Code | Complete codebase hosted on GitHub |
| Documentation | 18 technical documents (this `docs/` directory) |
| Dissertation | Final-year project report |
| Prototype Demo | Working demonstration of the SEAM framework |
| Evaluation Report | Experimental results and analysis |

## 8. Timeline (High-Level)

| Phase | Description | Target |
|-------|-------------|--------|
| Phase 0 | Project structure & documentation | Current |
| Phase 1 | Core infrastructure (RAG, ChromaDB, Knowledge) | TBD |
| Phase 2 | Agent scaffolding & Supervisor state machine | TBD |
| Phase 3 | Individual agent implementation | TBD |
| Phase 4 | Integration, testing & evaluation | TBD |
| Phase 5 | Deployment & final experiments | TBD |

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM output quality insufficient | Medium | High | Use domain-specific prompts; leverage RAG for context |
| Orchestration complexity | High | Medium | Incremental development; start with simple state machine |
| ChromaDB performance at scale | Low | Medium | Benchmark early; tune chunk size and collection design |
| Scope creep | Medium | High | Strict adherence to six-agent architecture; phase gates |

## 10. Success Criteria

1. All six agents are implemented and can be invoked by the Supervisor.
2. The Supervisor demonstrates dynamic task routing (not static sequencing).
3. RAG retrieval provides measurably relevant context to agents.
4. Continuous learning is demonstrated via the knowledge repository.
5. The system passes defined quality benchmarks.
6. A complete dissertation is submitted with reproducible experiments.
