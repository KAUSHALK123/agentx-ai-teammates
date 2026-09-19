# AgentX Sales n8n Workflow (`sales_process_lead`)

## Overview

- **Workflow Name**: Sales — Process Lead
- **Workflow ID**: `sales_process_lead`
- **Purpose**: Execute deterministic multi-step commercial lead qualification, status updates, and personalized outreach proposal generation.
- **Webhook Path**: `agentx-sales-process-lead`
- **Full Webhook Endpoint**: `http://<n8n-host>:<port>/webhook/agentx-sales-process-lead`
- **HTTP Method**: `POST`
- **Allowed Agent**: `sales`
- **Risk Level**: `LOW` (Drafts proposal; actual email dispatch is handled by `sales_send_followup` under Human-in-the-Loop approval gate).

---

## Architectural Responsibility Split

```
AgentX Frontend
      ↓
AgentX FastAPI Backend
      ↓
Sales Teammate (Agent Intelligence & Planning)
      ↓
Tool Execution Service (N8nProcessLeadTool)
      ↓
n8n Sales Workflow (Deterministic 7-Stage Execution)
      ↓
Business Record Update & Follow-Up Drafting
      ↓
n8n Structured Result
      ↓
AgentX Verification Engine
      ↓
Frontend Dashboard
```

1. **AgentX**: Responsible for understanding user intent, selecting the Sales teammate, determining business context, managing task state, and enforcing Human-in-the-Loop policy approvals.
2. **n8n Workflow Engine**: Responsible for deterministic data extraction, field validation, score and tier computation, business record synchronization, and output normalization.

---

## Node Sequence & Pipeline Breakdown

The refactored Sales workflow consists of 7 sequential, deterministic nodes:

| Stage | Node Name | Node Type | Purpose | Input | Output | Endpoint / Dependency |
|-------|-----------|-----------|---------|-------|--------|----------------------|
| **1** | `Webhook Trigger` | `n8n-nodes-base.webhook` | Listens for incoming POST requests from AgentX. | Raw HTTP POST payload | `$input.item.json` | `/webhook/agentx-sales-process-lead` |
| **2** | `Validate Request Payload` | `n8n-nodes-base.code` | Validates required `lead_id` and `task_id`/`request_id`. Routes invalid requests to structured error response. | Raw request body | `{ is_valid: bool, request_id, task_id, lead_id }` | None |
| **3** | `Retrieve Lead Data` | `n8n-nodes-base.code` | Extracts and normalizes lead fields (`name`, `email`, `company`, `source`, `notes`). | Validated payload | `{ is_valid, lead: { id, name, email, company, source, notes } }` | Local Data Context |
| **4** | `Process Sales Action` | `n8n-nodes-base.code` | Evaluates commercial criteria: computes qualification score (88 vs 70), tier (`TIER_1_ENTERPRISE` vs `TIER_2_GROWTH`), and rationale. | Normalized lead object | `{ qualification: { score, tier, status, rationale } }` | Deterministic Rules Engine |
| **5** | `Update Business Record` | `n8n-nodes-base.code` | Updates CRM lead status to `QUALIFIED` and records activity audit logs. | Qualification result | `{ lead_status: "qualified", record_updated: true, actions: [...] }` | Business Data Service |
| **6** | `Prepare Follow-up Result` | `n8n-nodes-base.code` | Prepares personalized follow-up outreach proposal (`prepared: true`, recipient, subject, message). | Updated business context | `{ follow_up: { prepared, recipient_name, recipient_email, subject, message } }` | Outreach Template Engine |
| **7** | `Format Respond to Webhook` | `n8n-nodes-base.code` | Assembles final structured JSON response returned to AgentX. | Processed lead data | Final structured JSON | Respond to AgentX Webhook |

---

## Webhook Contract

### 1. Request Payload Schema

```json
{
  "task_id": "task_sales_exec_001",
  "request_id": "req_sales_001",
  "action": "process_lead",
  "agent_id": "sales",
  "workflow_id": "sales_process_lead",
  "lead_id": "LEAD-001",
  "lead": {
    "id": "LEAD-001",
    "name": "Rajesh Khanna",
    "email": "rajesh@cyberdyne.co.in",
    "company": "Cyberdyne Tech",
    "source": "inbound_enterprise",
    "notes": "Inquired about 500 seat enterprise expansion"
  },
  "context": {}
}
```

### 2. Success Response Format (HTTP 200)

```json
{
  "success": true,
  "request_id": "req_sales_001",
  "task_id": "task_sales_exec_001",
  "workflow": "sales_process_lead",
  "status": "completed",
  "lead_id": "LEAD-001",
  "lead_status": "qualified",
  "lead": {
    "id": "LEAD-001",
    "name": "Rajesh Khanna",
    "email": "rajesh@cyberdyne.co.in",
    "company": "Cyberdyne Tech",
    "source": "inbound_enterprise",
    "notes": "Inquired about 500 seat enterprise expansion"
  },
  "qualification": {
    "score": 88,
    "tier": "TIER_1_ENTERPRISE",
    "status": "qualified",
    "rationale": "High-value enterprise prospect with 500+ seat potential"
  },
  "actions": [
    "Lead context retrieved and validated",
    "Commercial qualification evaluated (Score: 88, TIER_1_ENTERPRISE)",
    "Lead status updated to QUALIFIED in business record",
    "Personalized outreach proposal prepared"
  ],
  "follow_up": {
    "prepared": true,
    "recipient_name": "Rajesh Khanna",
    "recipient_email": "rajesh@cyberdyne.co.in",
    "subject": "Tailored Enterprise Solution for Cyberdyne Tech",
    "message": "Hello Rajesh Khanna,\n\nThank you for reaching out..."
  },
  "result": {
    "lead_id": "LEAD-001",
    "lead_status": "qualified",
    "tier": "TIER_1_ENTERPRISE",
    "score": 88
  },
  "errors": [],
  "timestamp": "2026-09-19T10:55:00.000Z"
}
```

### 3. Error Response Format (HTTP 200 / Validation Failure)

```json
{
  "success": false,
  "request_id": "req_sales_invalid",
  "task_id": "task_sales_invalid",
  "workflow": "sales_process_lead",
  "status": "failed",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Missing required field: lead_id"
  },
  "errors": [
    "Missing required field: lead_id"
  ],
  "timestamp": "2026-09-19T10:56:00.000Z"
}
```

---

## Environment Variables & Configuration

The following settings configure AgentX → n8n integration (`app/config/settings.py`):

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `N8N_BASE_URL` | `http://localhost:32768` | Base URL of the running n8n Docker instance. Auto-discovers mapped host port if connection fails. |
| `N8N_API_KEY` | None (Optional) | Optional header secret (`X-N8N-API-KEY`) for secure production authentication. |
| `N8N_WEBHOOK_TIMEOUT_SECONDS` | `15.0` | Timeout in seconds for n8n workflow execution requests. |
| `N8N_RETRY_ATTEMPTS` | `2` | Number of retries on transient connection or timeout failures. |

---

## Local Deployment & Verification

To import, publish, and test the Sales workflow locally against the running n8n Docker container:

```bash
python scripts/setup_n8n_workflows.py
```

To execute the backend unit and integration test suite:

```bash
pytest tests/test_n8n.py
```
