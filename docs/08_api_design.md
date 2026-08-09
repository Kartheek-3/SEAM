# 08 — API Design

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Overview

The SEAM backend exposes a RESTful API via FastAPI. All endpoints are prefixed
with `/api/v1`. Real-time status updates are delivered via WebSocket.

**Base URL:** `http://localhost:8000/api/v1`

## 2. API Endpoints

### 2.1 Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/projects` | Create a new project |
| `GET` | `/projects` | List all projects |
| `GET` | `/projects/{id}` | Get project details |
| `DELETE` | `/projects/{id}` | Delete a project |
| `POST` | `/projects/{id}/start` | Start project execution |
| `POST` | `/projects/{id}/stop` | Stop project execution |

### 2.2 Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/agents` | List all agents and their status |
| `GET` | `/agents/{agent_id}/status` | Get a specific agent's current status |

### 2.3 Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/{id}/tasks` | List tasks for a project |
| `GET` | `/projects/{id}/tasks/{task_id}` | Get task details and output |

### 2.4 Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/{id}/artifacts` | List generated artifacts |
| `GET` | `/projects/{id}/artifacts/{artifact_id}` | Get artifact content |

### 2.5 Knowledge

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/knowledge` | List knowledge entries |
| `POST` | `/knowledge/search` | Search knowledge via RAG |
| `GET` | `/knowledge/{id}` | Get a specific knowledge entry |

### 2.6 Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | System health check |
| `GET` | `/health/ollama` | Ollama connectivity check |
| `GET` | `/health/chromadb` | ChromaDB connectivity check |

## 3. WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{project_id}` | Real-time project status updates |

### WebSocket Message Format

```json
{
  "type": "status_update",
  "project_id": "string",
  "timestamp": "ISO-8601",
  "data": {
    "phase": "string",
    "agent": "string",
    "task_id": "string",
    "status": "string",
    "progress": 0.0,
    "message": "string"
  }
}
```

## 4. Request/Response Examples

### Create Project

**Request:**
```http
POST /api/v1/projects
Content-Type: application/json

{
  "name": "E-Commerce Platform",
  "description": "Build a REST API for an e-commerce platform with user auth, product catalog, and order management.",
  "technology_preferences": ["Python", "FastAPI", "PostgreSQL"],
  "constraints": ["Must support JWT authentication"]
}
```

**Response:**
```json
{
  "id": "proj-001",
  "name": "E-Commerce Platform",
  "status": "created",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Start Project

**Request:**
```http
POST /api/v1/projects/proj-001/start
```

**Response:**
```json
{
  "id": "proj-001",
  "status": "running",
  "current_phase": "ANALYSIS",
  "started_at": "2024-01-15T10:31:00Z"
}
```

## 5. Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Project description is required",
    "details": [
      {
        "field": "description",
        "issue": "Field is required"
      }
    ]
  }
}
```

## 6. Authentication

*Phase 0 note: Authentication is out of scope for the initial prototype.
API key-based auth may be added in later phases. See
[12_security.md](12_security.md).*

## 7. Rate Limiting

*Not implemented in Phase 0. To be considered for production deployment.*
