# AgentX — Autonomous AI Teammates for Business

AgentX is an autonomous AI workforce platform where specialized AI teammates (Support, Sales, Operations) understand business requests, formulate execution plans, execute actions through controlled tools, verify results against business criteria, and complete tasks or escalate to humans.

---

## Architecture Overview

```text
User Request
      ↓
AgentX API (FastAPI)
      ↓
Request Understanding (Intent analysis & parameter parsing)
      ↓
Agent Selection (Support / Sales / Operations via AgentRouter)
      ↓
Task Planning (Teammate formulates structured action plan)
      ↓
Tool Execution (Agent → Tool → Service → External System / ERP / CRM)
      ↓
Verification (TaskVerifier checks outcome correctness & safety constraints)
      ↓
Task Result (COMPLETED / ESCALATED / FAILED)
```

### Key Design Principles
1. **Agent Sandboxing**: AI agents never directly manipulate databases or external systems. All interactions follow the strict `Agent → Tool → Service → External System` boundary.
2. **Deterministic Verification**: Every tool outcome is evaluated by a verification layer before marking a task complete.
3. **Pluggable LLM Abstraction**: Structured with `BaseLLMProvider` so models (Gemini API, local LLMs, or mock providers) can be swapped without modifying agent implementations.
4. **Privacy-Preserving Audit Log**: Detailed execution stages (`CREATED`, `PLANNING`, `EXECUTING`, `VERIFYING`, `COMPLETED`) are tracked without exposing private chain-of-thought traces.

---

## Tech Stack

- **Runtime & Language**: Python 3.13+
- **API Framework**: FastAPI, Starlette
- **Server**: Uvicorn (ASGI)
- **Data Validation & Schemas**: Pydantic v2, Pydantic Settings
- **LLM Provider**: Google GenAI / Gemini API (with resilient fallback)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient
- **Database Readiness**: Modular repository pattern prepared for Supabase PostgreSQL

---

## Repository Structure

```text
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── config/
│   │   │   └── settings.py             # Pydantic environment configuration
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── health.py           # Health check endpoint
│   │   │       ├── tasks.py            # Task creation & status endpoints
│   │   │       ├── agents.py           # AI teammate inspection & routing
│   │   │       └── tools.py            # Tool discovery and execution endpoints
│   │   ├── agents/
│   │   │   ├── base.py                 # BaseAgent & TaskPlan abstractions
│   │   │   ├── support_agent.py        # Customer Support AI teammate
│   │   │   ├── sales_agent.py          # Commercial & Sales AI teammate
│   │   │   ├── operations_agent.py     # Logistics & Inventory AI teammate
│   │   │   └── router.py               # Explicit & automatic agent routing
│   │   ├── core/
│   │   │   └── llm.py                  # LLM provider abstraction (Gemini + fallback)
│   │   ├── models/
│   │   │   ├── task.py                 # Task, TaskStatus, ExecutionEvent domain models
│   │   │   └── business.py             # Customer, Order, Lead, Activity business models
│   │   ├── schemas/
│   │   │   ├── task.py                 # Request and response schemas for tasks
│   │   │   └── tool.py                 # Tool metadata & execution request/response schemas
│   │   ├── services/
│   │   │   ├── external_services.py    # Simulated legacy external APIs
│   │   │   ├── data_service.py         # Business data service abstraction & demo repo
│   │   │   ├── tool_executor.py        # Tool execution service, permissions, & audit logs
│   │   │   ├── task_store.py           # In-memory repository (Supabase-ready)
│   │   │   ├── verifier.py             # Verification & escalation layer
│   │   │   └── orchestrator.py         # End-to-end task lifecycle orchestrator
│   │   ├── tools/
│   │   │   ├── base.py                 # BaseTool & ToolResult abstractions
│   │   │   ├── registry.py             # Central ToolRegistry & provider interfaces
│   │   │   ├── implementations.py      # Working business tools (lookup, update, activity)
│   │   │   └── mock_tools.py           # Legacy mock tools
│   │   └── utils/
│   ├── tests/
│   │   ├── test_api.py                 # Health, routing, tool, and lifecycle tests
│   │   ├── test_agents.py              # AI Teammates, planning, and router tests
│   │   └── test_tools.py               # Tool registry, permissions, execution, and API tests
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                           # Frontend workspace placeholder (Phase 3+)
│   └── .gitkeep
│
├── docs/
│   └── architecture/
│       └── overview.md
│
├── tests/                              # Root integration tests placeholder
├── .gitignore
├── README.md
└── LICENSE                             # MIT License
```

---

## Local Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Git

### 2. Environment Configuration
Navigate to the `backend/` directory and configure environment variables:
```bash
cd backend
cp .env.example .env
```

Edit `.env` and set your Google Gemini API key if available:
```ini
AGENTX_ENV=development
PORT=8000
HOST=0.0.0.0
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: AgentX includes automated heuristic fallbacks for routing and execution if no API key is supplied, enabling smooth local offline development).*

### 3. Create Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## How to Run Backend

Start the development server with live reload:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The server will be available at:
- API Base: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`

---

## Running Tests

Execute the automated test suite with pytest:
```bash
cd backend
pytest tests -v
```

---

## Available API Endpoints

### 1. Health Check
- **`GET /health`**
- Returns system operational status, version, and environment.

### 2. Create and Run Task
- **`POST /tasks`**
- Submits a business request for autonomous execution.
- **Request Body**:
  ```json
  {
    "user_request": "We need custom pricing and enterprise volume discount for 500 seats",
    "selected_agent": "sales"
  }
  ```
  *(Note: `selected_agent` is optional. If omitted, `AgentRouter` automatically analyzes intent and routes to `support`, `sales`, or `operations`).*
- **Response (201 Created)**:
  ```json
  {
    "task_id": "task_4f8b9c2a1e3d",
    "selected_agent": "sales",
    "status": "COMPLETED"
  }
  ```

### 3. Retrieve Task Details
- **`GET /tasks/{task_id}`**
- Returns the complete lifecycle state, result payload, verification summary, and stage events.
- **Response (200 OK)**:
  ```json
  {
    "task_id": "task_4f8b9c2a1e3d",
    "user_request": "We need custom pricing and enterprise volume discount for 500 seats",
    "selected_agent": "sales",
    "status": "COMPLETED",
    "created_at": "2026-09-17T16:40:00Z",
    "updated_at": "2026-09-17T16:40:01Z",
    "result": {
      "summary": "Sales Teammate successfully resolved request.",
      "action_details": {
        "inquiry": "We need custom pricing and enterprise volume discount for 500 seats",
        "qualified": true,
        "tier": "Enterprise Tier",
        "recommended_plan": "Enterprise Annual",
        "discount_eligible": true
      },
      "verified": true,
      "verification_notes": "Action verified: outputs meet quality and data integrity constraints."
    },
    "error": null,
    "approval_required": false,
    "events": [
      {
        "current_stage": "CREATED",
        "action_performed": "Initialized business task",
        "tool_used": null,
        "status": "SUCCESS",
        "timestamp": "2026-09-17T16:40:00Z",
        "concise_result_summary": "Received request..."
      },
      {
        "current_stage": "PLANNING",
        "action_performed": "Assigned task to Sales Teammate (Commercial Account & Lead Specialist)",
        "tool_used": null,
        "status": "SUCCESS",
        "timestamp": "2026-09-17T16:40:00.1Z",
        "concise_result_summary": "Teammate identity established: Sales Teammate"
      },
      {
        "current_stage": "EXECUTING",
        "action_performed": "Tool 'lead_qualification' execution finished",
        "tool_used": "lead_qualification",
        "status": "SUCCESS",
        "timestamp": "2026-09-17T16:40:00.2Z",
        "concise_result_summary": "Successfully qualified sales lead and determined tier"
      },
      {
        "current_stage": "VERIFYING",
        "action_performed": "Verification completed",
        "tool_used": null,
        "status": "SUCCESS",
        "timestamp": "2026-09-17T16:40:00.3Z",
        "concise_result_summary": "Action verified: outputs meet quality and data integrity constraints."
      }
    ]
  }
  ```

### 4. List Tasks
- **`GET /tasks?limit=50`**
- Returns a list of recently created tasks and statuses.

### 5. List AI Teammates
- **`GET /agents`**
- Returns all specialized AI teammates (Support, Sales, Operations) along with their machine-readable capabilities, roles, and assigned tools.
- **Response (200 OK)**:
  ```json
  [
    {
      "agent_id": "support",
      "name": "Support Teammate",
      "role": "Customer Resolution & Support Specialist",
      "description": "Specialized AI teammate for resolving customer complaints...",
      "responsibilities": ["customer support", "complaints", "order/payment issue investigation", ...],
      "capabilities": [
        {"name": "investigate_customer_issue", "description": "...", "category": "investigation"},
        {"name": "analyze_complaint", "description": "...", "category": "analysis"},
        {"name": "identify_resolution", "description": "...", "category": "resolution"},
        {"name": "prepare_response", "description": "...", "category": "communication"},
        {"name": "escalate_issue", "description": "...", "category": "escalation"}
      ],
      "available_tools": ["ticket_lookup"]
    },
    ...
  ]
  ```

### 6. Inspect AI Teammate
- **`GET /agents/{agent_id}`**
- Returns the complete profile and capability specifications for a single teammate (`support`, `sales`, or `operations`). Returns `404 Not Found` if invalid.

### 7. Generate Structured Task Plan
- **`POST /tasks/plan`**
- Submits a business request for understanding, automatic or explicit routing, and structured execution plan generation without immediately invoking external tools.
- **Request Body**:
  ```json
  {
    "user_request": "Customer says their payment was successful but their order wasn't confirmed."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "task_id": "plan_7f1c84b12a3d",
    "selected_agent": "support",
    "task_category": "support",
    "confidence": 0.88,
    "explanation": "Request contains customer support, ticket, or refund resolution terminology.",
    "is_ambiguous": false,
    "clarification_prompt": null,
    "plan": {
      "task_id": "plan_7f1c84b12a3d",
      "agent": "support",
      "objective": "Investigate customer issue and formulate resolution...",
      "steps": [
        {
          "step_id": 1,
          "action": "Analyze customer issue details and extract account/order tokens",
          "type": "investigation",
          "status": "pending"
        },
        {
          "step_id": 2,
          "action": "Perform ticket and order lookup in customer support system",
          "type": "tool_action",
          "status": "pending"
        },
        {
          "step_id": 3,
          "action": "Verify payment/delivery status and evaluate escalation criteria",
          "type": "verification",
          "status": "pending"
        },
        {
          "step_id": 4,
          "action": "Synthesize customer response and prepare resolution record",
          "type": "synthesis",
          "status": "pending"
        }
      ]
    }
  }
  ```
- **Ambiguous Request Handling**:
  If the input lacks sufficient business clarity (e.g., `"asdf"`), the endpoint returns `is_ambiguous = true` with a polite `clarification_prompt` rather than mistakenly routing to the wrong teammate.

---

## Phase 4 — Tool & Data Layer

AgentX enforces strict sandboxing: **Agents never directly modify databases or external systems**. Every tool action traverses:
```text
Agent → Tool Execution Service → Permission Check → Tool → Data Service → Database / External APIs
```

### 1. Tool Registry & Read/Write Classification

All tools extend `BaseTool` with typed input and output schemas and explicit read/write classifications:

| Tool ID | Name | Category | Classification | Description |
| :--- | :--- | :--- | :--- | :--- |
| `lookup_customer` | Customer Lookup | `support` | **READ** | Find customer accounts by ID, email, phone, or name. |
| `lookup_order` | Order Lookup | `support` | **READ** | Retrieve order status and item details by order or customer ID. |
| `lookup_transaction` | Transaction Lookup | `support` | **READ** | Look up payment transactions, gateway refs, and settlement statuses. |
| `lookup_lead` | Lead Lookup | `sales` | **READ** | Search sales leads by lead ID, company, or contact email. |
| `update_lead` | Lead Update | `sales` | **WRITE** | Update CRM lead status, notes, or score. |
| `get_business_data` | Business Data Retrieval | `operations` | **READ** | Fetch business performance metrics, inventory, or operational KPIs. |
| `verify_record` | Record Verification | `operations` | **READ** | Cross-verify records across system layers (ledger vs gateway vs inventory). |
| `create_activity` | Activity Logger | `general` | **WRITE** | Create an audit activity log entry for a task or business event. |

### 2. Agent Permission Matrix

Agents are strictly restricted to their authorized toolset:

- **Customer Support Teammate (`support`)**:
  - `lookup_customer`, `lookup_order`, `lookup_transaction`, `create_activity`
- **Sales Teammate (`sales`)**:
  - `lookup_customer`, `lookup_lead`, `update_lead`, `create_activity`
- **Operations Teammate (`operations`)**:
  - `get_business_data`, `verify_record`, `create_activity`

Any attempt by an agent to execute an unauthorized tool raises `403 Forbidden` and is permanently logged in the audit trail.

### 3. Tool Endpoints

#### List Available Tools
- **`GET /tools`** (or `GET /tools?category=support`)
- Returns registered tools with schemas, categories, and `is_write` classifications.

#### Inspect Tool Metadata
- **`GET /tools/{tool_id}`**
- Returns schema and metadata for a specific tool.

#### Controlled Tool Execution
- **`POST /tools/{tool_id}/execute`**
- Manually executes a registered tool under the identity and permissions of the specified agent.
- **Request**:
  ```json
  {
    "agent_id": "support",
    "parameters": {
      "customer_id": "CUST-001"
    },
    "task_id": "optional_task_id"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "tool_id": "lookup_customer",
    "agent_id": "support",
    "data": {
      "customer_id": "CUST-001",
      "name": "Alice Sharma",
      "email": "alice.sharma@example.com",
      "phone": "+91-9876543210",
      "status": "active"
    },
    "error": null,
    "message": "Found customer Alice Sharma (CUST-001)"
  }
  ```

---

## Phase 5 — Task Execution & Verification

Phase 5 equips AgentX with the capability to autonomously execute planned multi-step workflows.

### 1. Multi-Step Execution Lifecycle

```text
UNDERSTAND → DECIDE → PLAN → ACT → VERIFY → COMPLETE
```

The `TaskExecutionEngine` orchestrates each step:
1. **Sequential Step Progression**: Steps transition strictly through `PENDING → RUNNING → COMPLETED` (or `FAILED` / `SKIPPED`).
2. **Context & Variable Propagation**: Entities retrieved in earlier steps (e.g. `customer_id`, `order_id`, `lead_id`) are safely injected into subsequent step inputs via `ExecutionContext`.
3. **Transient Retry Resilience**: Transient failures are retried up to 2 times, while security, schema, and unauthorized tool rejections fail fast without blind retries.
4. **Mandatory Write Verification**: Write operations (`update_lead`, `create_activity`) are checked against the actual persistence layer before declaring a task completed.
5. **Human Escalation**: Heuristics detect operational discrepancies or critical thresholds (e.g. low stock, urgent priority) and transition tasks to `ESCALATED`.

### 2. Execution Endpoints

#### Execute a Planned Task
- **`POST /tasks/{task_id}/execute`**
- Executes the planned steps sequentially through the assigned AI teammate and controlled tools.
- **Response**:
  ```json
  {
    "task_id": "plan_c3fdb8c6966d",
    "status": "COMPLETED",
    "selected_agent": "support",
    "final_result": {
      "task_id": "plan_c3fdb8c6966d",
      "status": "COMPLETED",
      "summary": "Support Teammate successfully resolved request.",
      "actions_performed": [
        "Step 1 (Lookup customer profile): Found customer Alice Sharma (CUST-001)",
        "Step 2 (Retrieve customer order fulfillment): Found 2 orders for customer CUST-001",
        "Step 3 (Lookup payment transaction): Found transaction TXN-5001 for order ORD-5001",
        "Step 5 (Log resolution activity): Created activity log act_8f29d10e for task"
      ],
      "verification": {
        "verified": true,
        "verification_type": "record_match",
        "summary": "All planned actions executed and verified against data store."
      }
    },
    "error": null,
    "message": "Task execution completed with status: COMPLETED"
  }
  ```

#### Inspect Complete Execution Trace
- **`GET /tasks/{task_id}/execution`**
- Returns the complete execution trace for frontend visualization, including step statuses, timestamps, tool invocation records, and verification status.

### 3. Tested Business Flows

- **Support Flow**: `"Investigate customer C001's order."`
  - `lookup_customer` → `lookup_order` → `lookup_transaction` → `verification` → `COMPLETED`
- **Sales Flow**: `"Process lead L001 and update the lead status."`
  - `lookup_lead` → qualification analysis → `update_lead` → secondary verification → `create_activity` → `COMPLETED`
- **Operations Flow**: `"Check today's business data and identify anything requiring attention."`
  - `get_business_data` → analysis → `verify_record` → discrepancy identification → `ESCALATED`
