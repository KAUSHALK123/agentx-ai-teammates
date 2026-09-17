# AgentX Architecture Overview

AgentX is an autonomous AI workforce platform where specialized AI teammates understand business requests, plan actions, execute through tools, verify results, and complete tasks or escalate to a human.

## Core Flow

```text
User Request
      ↓
AgentX API (FastAPI)
      ↓
Request Understanding (Intent classification & parameter extraction)
      ↓
Agent Selection (Support / Sales / Operations via AgentRouter)
      ↓
Task Planning (Agent creates actionable execution steps)
      ↓
Tool Execution (Agent → Tool → Service → External System / Database)
      ↓
Verification (TaskVerifier checks outcome correctness against expectations)
      ↓
Task Result (Completed / Escalated / Failed)
```

## Modular Layers

1. **API Layer (`backend/app/api/`)**: Clean REST endpoints (`POST /tasks`, `GET /tasks/{task_id}`, `GET /health`).
2. **Core Abstractions (`backend/app/core/`)**: Pluggable LLM interface with Gemini implementation and heuristic fallback.
3. **Agent Layer (`backend/app/agents/`)**: Specialized teammate profiles (`SupportAgent`, `SalesAgent`, `OperationsAgent`) and `AgentRouter`.
4. **Tool Layer (`backend/app/tools/`)**: Sandboxed, decoupled tools following the `Agent → Tool → Service` pattern.
5. **Verification Layer (`backend/app/services/verifier.py`)**: Post-execution outcome inspection before completion.
6. **Task Store (`backend/app/services/task_store.py`)**: Clean repository abstraction ready for Supabase PostgreSQL.
