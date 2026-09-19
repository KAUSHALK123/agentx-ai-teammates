# AgentX Cognee Knowledge Base & Retrieval Architecture

This document provides a comprehensive guide to the **Cognee Knowledge Base** integrated into **AgentX — Autonomous AI Teammates for Business**.

---

## 1. Architecture Overview

AgentX uses **Cognee** as its persistent semantic knowledge engine. It indexes business policies, FAQs, product catalogs, and operational rules into vector and graph representations for fast and context-rich retrieval.

```
                   Demo Business Knowledge (.md)
                                ↓
                        Ingestion Manager
                                ↓
                      Cognee Engine (LanceDB / Graph)
                                ↓
                         CogneeProvider
                                ↓
                         KnowledgeService
                                ↓
                       LookupKnowledgeTool
                                ↓
               ┌────────────────┼────────────────┐
               ↓                ↓                ↓
         Support Agent     Sales Agent    Operations Agent
               ↓
        Policy-Aware Result
     (with knowledge_used context)
```

### Core Design Principles
- **Decoupled Architecture:** Agents call `KnowledgeService` or `LookupKnowledgeTool`, avoiding direct import coupling with Cognee across the codebase.
- **Provider Pattern (`IKnowledgeProvider`):** Abstract interface that defaults to `CogneeProvider`, enabling future providers (PDFs, Databases, MCP) without altering agent code.
- **Explicit Knowledge Context (`knowledge_used`):** Context retrieved for a task is attached to `TaskResult.result["knowledge_used"]` with source metadata (`source`, `content`, `score`, `query`), enabling frontend inspection without exposing internal agent thoughts.
- **Graceful Failure:** If Cognee service or vector storage is unavailable, `KnowledgeService` safely catches exceptions and returns an empty/unavailable result, ensuring AgentX core functionality remains operational.

---

## 2. Environment Variables & Setup

Add the following environment configuration to `backend/.env` (refer to `backend/.env.example`):

```bash
# Cognee Knowledge Base Engine Configuration
COGNEE_DATA_DIR=backend/app/knowledge/data
COGNEE_DATASET_NAME=demo_business_knowledge
COGNEE_EMBEDDING_PROVIDER=fastembed
COGNEE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
COGNEE_VECTOR_DB_PROVIDER=lancedb
COGNEE_LLM_PROVIDER=gemini
```

---

## 3. Knowledge Base Directory Structure

Demo business data resides in `backend/app/knowledge/data/`:

```
backend/app/knowledge/
├── data/
│   ├── refund_policy.md        # Eligibility, windows, approvals ($500+ threshold)
│   ├── return_policy.md        # Return windows, condition requirements, RMA steps
│   ├── support_policy.md       # Ticket severity (SEV-1 to SEV-3), SLAs, escalations
│   ├── sales_guidelines.md     # Lead qualification (B2B, $10k+ ARR), priority, enterprise rules
│   ├── product_catalog.md      # Fictional AgentX products, tiers, pricing, specs
│   ├── operations_rules.md     # Inventory thresholds, delivery delays, incident escalation
│   └── faq.md                  # Common customer & business Q&A
├── ingestion/
│   └── ingest.py               # Repeatable, hash-based ingestion manager
├── service/
│   └── knowledge_service.py    # KnowledgeService & CogneeProvider implementation
├── tools/
│   └── knowledge_tools.py      # LookupKnowledgeTool wrapper for agent execution
└── tests/
    └── test_knowledge.py       # Test suite for retrieval and agent policy context
```

---

## 4. Ingesting Demo Knowledge

The ingestion process reads markdown files in `backend/app/knowledge/data/`, checks SHA256 hashes against previous indexing runs to prevent duplicate processing, and indexes chunks into Cognee.

### Command Line Ingestion:

To run ingestion from the `backend` directory:

```bash
python -m app.knowledge.ingest
```

### Python API Ingestion:

```python
import asyncio
from app.knowledge.ingest import ingest_demo_knowledge

async def main():
    summary = await ingest_demo_knowledge(force=False)
    print("Ingestion Summary:", summary)

asyncio.run(main())
```

---

## 5. KnowledgeService & API Usage

### Python Service API

```python
from app.knowledge.service import get_knowledge_service

service = get_knowledge_service()
result = await service.search(query="What is the refund policy for delayed orders?", limit=3)

print("Available:", result.available)
for item in result.results:
    print(f"Source: {item.source} (Score: {item.score:.2f})")
    print(f"Content: {item.content}")
```

### FastAPI Endpoints

#### 1. Search Knowledge Base
- **POST** `/api/v1/knowledge/search` (also available at `/knowledge/search`)
- **Request:**
  ```json
  {
    "query": "What is the refund policy for delayed orders?",
    "limit": 3
  }
  ```
- **Response:**
  ```json
  {
    "query": "What is the refund policy for delayed orders?",
    "total_count": 1,
    "available": true,
    "error": null,
    "results": [
      {
        "content": "Refund Policy ... Orders delayed beyond 14 business days qualify for 100% refund.",
        "source": "refund_policy.md",
        "score": 0.89,
        "metadata": {"dataset": "demo_business_knowledge"}
      }
    ]
  }
  ```

#### 2. Get Knowledge System Status
- **GET** `/api/v1/knowledge/status` (also available at `/knowledge/status`)
- **Response:**
  ```json
  {
    "status": "online",
    "cognee_available": true,
    "data_dir": "backend/app/knowledge/data",
    "total_indexed_documents": 7
  }
  ```

---

## 6. Support Agent Policy Integration

The `SupportAgent` includes `lookup_knowledge` in its default tool set. When tasked with customer support requests, it plans policy lookup steps, retrieves context from Cognee, and includes explicit metadata in its execution result:

```json
{
  "task_id": "task_123",
  "status": "completed",
  "result": {
    "summary": "Customer is eligible for a full refund under the delayed order policy.",
    "knowledge_used": [
      {
        "source": "refund_policy.md",
        "content": "Orders delayed by more than 14 business days qualify for 100% refund without restocking fees.",
        "score": 0.88,
        "query": "delayed order refund policy"
      }
    ]
  }
}
```

---

## 7. Verifying Retrieval & Running Tests

To run the complete knowledge base test suite:

```bash
cd backend
pytest tests/test_knowledge.py -v
```

All backend tests can also be validated:

```bash
pytest tests/ -v
```

---

## 8. Future n8n Integration Note

Cognee operates as the core **knowledge & memory layer**, whereas n8n handles **action execution and external workflows**. In future phases:
- `AgentX → KnowledgeService → Cognee` handles policy retrieval and knowledge graph lookups.
- `AgentX → Tool Layer → n8n` handles external workflow triggers (e.g., executing refund payments via Payment Gateway).
- n8n workflows may optionally query Cognee via standard REST endpoints (`POST /api/v1/knowledge/search`).
