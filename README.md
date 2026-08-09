# SEAM — Self-Evolving Autonomous Multi-Agent Framework

> A domain-aware, adaptive multi-agent framework for end-to-end software engineering.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-green.svg)]()
[![React + Vite](https://img.shields.io/badge/React-Vite-purple.svg)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-latest-orange.svg)]()

---

## Overview

SEAM is a final-year research project that investigates whether a multi-agent
system—composed of specialised, collaborating AI agents—can autonomously handle
the complete software-engineering lifecycle: requirements analysis, architecture
design, code generation, quality assurance, and delivery.

Unlike static pipeline approaches, SEAM features a **Supervisor/Orchestrator**
that dynamically assigns tasks, evaluates intermediate results, and triggers
rework when quality gates are not met. The system continuously learns by
persisting validated knowledge in an **Organizational Knowledge Repository**
backed by ChromaDB and a RAG (Retrieval-Augmented Generation) pipeline.

## Key Features

| Feature | Description |
|---------|-------------|
| **Six-Agent Architecture** | Analysis, Planning & Design, Supervisor/Orchestrator, Coding, QA, and Delivery agents |
| **Dynamic Orchestration** | Supervisor supports dependency checking, task assignment, and QA-driven rework |
| **Shared RAG Infrastructure** | Retrieval-Augmented Generation as shared infrastructure, not an independent agent |
| **Continuous Learning** | Validated knowledge stored and reused via the organizational knowledge repository |
| **Domain Awareness** | Agents leverage domain-specific context from the knowledge repository |
| **Local-First LLMs** | Powered by Ollama with DeepSeek-Coder and Llama 3.1 |

## Architecture (High Level)

```
┌────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)              │
└──────────────────────────┬─────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼─────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │           Supervisor / Orchestrator                │  │
│  │         (LangGraph State Machine)                  │  │
│  └──┬──────┬──────┬──────┬──────┬──────┬─────────────┘  │
│     │      │      │      │      │      │                 │
│  ┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐            │
│  │Analy││Plan ││Code ││ QA  ││Deli ││ ... │            │
│  │sis  ││& Des││     ││     ││very ││     │            │
│  └──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└─────┘            │
│     │      │      │      │      │                        │
│  ┌──▼──────▼──────▼──────▼──────▼──────────────────┐    │
│  │         Shared Infrastructure                    │    │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │    │
│  │  │   RAG   │  │ ChromaDB │  │  Org Knowledge │  │    │
│  │  └─────────┘  └──────────┘  └────────────────┘  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
SEAM/
├── frontend/          # React + Vite UI
├── backend/           # FastAPI application server
├── agents/            # Six executable agent modules
├── orchestration/     # Supervisor/Orchestrator logic (LangGraph)
├── rag/               # Shared RAG infrastructure
├── knowledge/         # Organizational knowledge repository
├── prompts/           # Prompt templates for all agents
├── tests/             # Unit, integration, and end-to-end tests
├── evaluation/        # Benchmarks, metrics, and experiment scripts
├── deployment/        # Docker, CI/CD, and deployment configs
├── docs/              # Project documentation (18 documents)
├── README.md
├── .gitignore
├── .env.example
└── requirements.txt
```

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Backend | FastAPI |
| Frontend | React + Vite |
| Agent Orchestration | LangGraph, LangChain |
| Vector Store | ChromaDB |
| LLM Runtime | Ollama |
| Models | DeepSeek-Coder, Llama 3.1 |
| Data Validation | Pydantic |
| HTTP Client | Requests |
| Configuration | python-dotenv |
| Version Control | Git / GitHub |
| Containerisation | Docker |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Ollama installed and running
- Docker (optional, for containerised deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/SEAM.git
cd SEAM

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Pull required Ollama models
ollama pull deepseek-coder
ollama pull llama3.1

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running the Application

```bash
# Start the backend
uvicorn backend.main:app --reload --port 8000

# In a separate terminal, start the frontend
cd frontend
npm run dev
```

## Development Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 0** | Project structure & documentation | ✅ Current |
| **Phase 1** | Core infrastructure (RAG, ChromaDB, Knowledge Repo) | 🔲 Planned |
| **Phase 2** | Agent scaffolding & Supervisor state machine | 🔲 Planned |
| **Phase 3** | Individual agent implementation | 🔲 Planned |
| **Phase 4** | Integration, testing & evaluation | 🔲 Planned |
| **Phase 5** | Deployment & final experiments | 🔲 Planned |

## Documentation

All project documentation lives in [`docs/`](docs/). See the
[documentation index](docs/README.md) for a full listing.

## Contributing

This is a final-year research project. Contributions are managed through the
project supervisor. Please follow the coding standards and commit conventions
documented in the project charter.

## License

This project is developed as part of an academic research programme.
Licensing terms will be determined upon completion.

---

*SEAM — because the best software feels seamless.*
