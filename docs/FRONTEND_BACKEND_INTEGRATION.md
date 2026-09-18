# Frontend & Backend Integration Contract — AgentX

This document defines the interface, contract specifications, and lifecycle patterns connecting the React Command Center frontend with the AgentX FastAPI backend (Phases 1–10).

---

## 1. Architectural Principles

1. **Centralized Orchestration**:
   - The React frontend communicates exclusively with the AgentX FastAPI backend (`http://localhost:8000`).
   - The frontend **NEVER** communicates directly with n8n or external execution providers.
   - Flow: `React Frontend → AgentX FastAPI Backend → Agent Router → AI Teammate (Support/Sales/Operations) → Tool Execution Layer → Verification Engine → Result`.

2. **Backend as Source of Truth**:
   - Human approvals/rejections are never resolved purely client-side; every decision round-trips to `POST /approvals/{approval_id}/approve` or `POST /approvals/{approval_id}/reject`.
   - Task planning, routing, tool invocation, and verification occur in the backend.

3. **Multimodal Inputs**:
   - File uploads (PDF, CSV, DOCX, images, audio) use `POST /inputs/upload` to store, extract structured data, and obtain an `input_id`.
   - The returned `input_id` is passed inside `input_ids` to `POST /tasks`.

---

## 2. Environment Configuration

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` (or `""` using proxy) | AgentX backend base URL |
| `CORS_ORIGINS` (Backend) | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins for CORS |

In Vite local development (`npm run dev`), requests to `/api`, `/tasks`, `/agents`, `/tools`, `/approvals`, `/inputs`, `/support`, `/health`, and `/integrations` are proxied to `http://localhost:8000`.

---

## 3. Endpoints & Schemas Summary

### 3.1 System Health
- **Endpoint**: `GET /health` (or `GET /api/v1/health`)
- **Response**:
```json
{
  "status": "healthy",
  "app_name": "AgentX — Autonomous AI Teammates",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-09-18T17:00:00Z"
}
```

### 3.2 AI Teammates
- **List Agents**: `GET /agents`
- **Get Agent Details**: `GET /agents/{agent_id}` (`support`, `sales`, `operations`)
- **Response**:
```json
[
  {
    "agent_id": "support",
    "name": "Support Teammate",
    "role": "support",
    "description": "Autonomous customer support specialist...",
    "responsibilities": ["Customer sentiment analysis", "Refund verification"],
    "capabilities": ["sentiment_analysis", "order_investigation", "refund_evaluation"],
    "available_tools": ["customer_crm_api", "order_tracking_api", "refund_processor"]
  }
]
```

### 3.3 Task Lifecycle
- **Create & Run Task**: `POST /tasks`
  - **Request**:
  ```json
  {
    "user_request": "Investigate customer complaint for Order #ORD-8821",
    "selected_agent": "support", // optional: null for automatic routing
    "input_ids": ["inp_9042a1b2c3d4"] // optional: attached input files
  }
  ```
  - **Response**: `201 Created`
  ```json
  {
    "task_id": "task_abc12345",
    "selected_agent": "support",
    "status": "EXECUTING"
  }
  ```

- **Generate Execution Plan**: `POST /tasks/plan`
  - **Request**: `{ "user_request": "...", "selected_agent": "sales" }`
  - **Response**: `TaskPlanResponse` containing steps, tools, and objectives.

- **Execute Planned Task**: `POST /tasks/{task_id}/execute`
  - Resumes or runs the task plan through the execution engine.

- **Get Task Details**: `GET /tasks/{task_id}`
  - Returns task status, lifecycle events, and final result.

- **Get Live Execution Trace**: `GET /tasks/{task_id}/execution`
  - **Response**:
  ```json
  {
    "task_id": "task_abc12345",
    "task_status": "COMPLETED",
    "selected_agent": "support",
    "current_step": null,
    "steps": [
      {
        "step_id": "step-1",
        "description": "Extract customer intent and verify order status",
        "tool_name": "order_tracking_api",
        "required_approval": false
      }
    ],
    "execution_records": [
      {
        "step_id": "step-1",
        "tool_name": "order_tracking_api",
        "start_time": "2026-09-18T17:00:01Z",
        "end_time": "2026-09-18T17:00:02Z",
        "status": "SUCCESS",
        "output_result": { "status": "delayed", "order_id": "ORD-8821" }
      }
    ],
    "verification_status": {
      "verified": true,
      "criteria_checked": ["Order ID exists", "Carrier delay confirmed"],
      "risk_score": 0.1,
      "notes": "All checks passed."
    },
    "approval": null,
    "final_result": { "summary": "Investigation completed. Apology dispatched." }
  }
  ```

- **List Tasks**: `GET /tasks?limit=50`
  - Returns recent tasks for history and dashboard.

### 3.4 Human Approvals
- **List Pending Approvals**: `GET /approvals/pending` (or `GET /approvals?status=PENDING`)
- **Get Approval by ID**: `GET /approvals/{approval_id}`
- **List Approvals for Task**: `GET /approvals/task/{task_id}`
- **Approve Action**: `POST /approvals/{approval_id}/approve?resolved_by=operator`
  - Unblocks the task execution engine to execute the high-risk tool and continue to verification.
- **Reject Action**: `POST /approvals/{approval_id}/reject?resolved_by=operator`
  - **Request**: `{ "reason": "Operator rejected price tier" }`
  - Stops task execution with `ESCALATED` status.

### 3.5 Multimodal Business Inputs (Phase 10)
- **Upload File**: `POST /inputs/upload` (`multipart/form-data`)
  - **Form Fields**: `file` (Binary), `task_id` (optional string)
  - **Supported Types**: PDF, CSV, DOCX, PNG, JPEG, WEBP, MP3, WAV, M4A, Text
  - **Response**: `201 Created`
  ```json
  {
    "input_id": "inp_c123456789ab",
    "type": "PDF",
    "filename": "customer_invoice.pdf",
    "size_bytes": 102400,
    "status": "PROCESSED",
    "metadata": { "page_count": 2 }
  }
  ```
- **Get Input Details**: `GET /inputs/{input_id}`
  - Returns `extracted_text`, `structured_data`, status, and metadata.
- **Process / Re-extract**: `POST /inputs/{input_id}/process`
- **Get Task Inputs**: `GET /tasks/{task_id}/inputs`

### 3.6 Support Review & Resolution
- **Analyze Support Message**: `POST /support/analyze`
  - **Request**: `{ "message": "Customer complaint...", "customer_id": "C-902" }`
  - **Response**: Sentiment, intent, severity, customer context, recommended action, and response options.
- **List Support Cases**: `GET /support/cases`
- **Get Support Case**: `GET /support/cases/{case_id}`
- **Execute Support Action**: `POST /support/execute-action`
  - **Request**:
  ```json
  {
    "task_id": "task_abc12345",
    "action": "Offer Compensation",
    "custom_response": "Issued $25 store credit voucher"
  }
  ```

### 3.7 Tools & Integrations
- **List Tools**: `GET /tools`
- **Get Tool**: `GET /tools/{tool_id}`
- **n8n Status**: `GET /integrations/n8n/status`
  - Returns health and configured workflows without exposing direct n8n webhook URLs to React.

---

## 4. Frontend Integration Layer Structure

```
frontend/src/
├── api/
│   ├── client.ts         # Centralized Fetch client with error handling & base URL
│   ├── agents.ts         # Agent directory & capability queries
│   ├── tasks.ts          # Task creation, planning, execution trace, polling
│   ├── approvals.ts      # Pending approvals, approve & reject actions
│   ├── inputs.ts         # Multimodal file upload & extraction queries
│   ├── support.ts        # Support review analysis & interactive execution
│   ├── tools.ts          # Tool registry & n8n status
│   ├── activity.ts       # Aggregated audit & activity feed
│   └── index.ts          # Barrel export
├── types/
│   ├── index.ts          # Frontend UI domain models (TaskItem, ExecutionStep, etc.)
│   └── api.ts            # Typed backend schemas matching Pydantic models
└── context/
    └── AppContext.tsx    # State management, initial load, polling, action dispatch
```

---

## 5. Error Format & Handling

All backend API errors return a standard JSON error envelope:
```json
{
  "detail": "Descriptive error message from AgentX backend"
}
```
The frontend `ApiClientError` class extracts `detail` or `message` and exposes the HTTP `status` code. UI components display clean alert banners when errors occur without crashing the page.
