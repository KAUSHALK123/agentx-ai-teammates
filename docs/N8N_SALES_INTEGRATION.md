# AgentX — n8n Sales Agent Integration Documentation

This document describes the integration architecture, configuration, tool specification, and execution flow for connecting the **AgentX Sales Agent** to the local **n8n Workflow Engine**.

---

## 1. System Architecture

The integration follows strict decoupled security and control boundaries:

```
+-------------------+
|  React Frontend   | (Vite / Port 3000)
+-------------------+
          |
          v (POST /api/v1/tasks)
+-------------------+
|  AgentX FastAPI   | (Python Host / Port 8000)
+-------------------+
          |
          v
+-------------------+
|    Sales Agent    | (Formulates execution plan with sales_process_lead)
+-------------------+
          |
          v
+-------------------+
|   Tool Executor   | (Applies permissions & invokes N8nToolProvider)
+-------------------+
          |
          v (HTTP POST /webhook/agentx-sales-process-lead)
+-------------------+
|    n8n Engine     | (Docker Container / Port 32768 -> 5678)
+-------------------+
          |
          v (Returns structured lead status & follow-up)
+-------------------+
|   AgentX Engine   | (Updates CRM, logs activity, verifies execution)
+-------------------+
          |
          v
+-------------------+
|  React Frontend   | (Renders real-time progress & completed result)
+-------------------+
```

---

## 2. Configuration Parameters

In `backend/app/config/settings.py` (or `.env`):

```ini
N8N_BASE_URL=http://localhost:32768
N8N_WEBHOOK_TIMEOUT_SECONDS=10.0
N8N_RETRY_ATTEMPTS=2
```

---

## 3. Dedicated Tool Specification

### Tool ID: `sales_process_lead`
- **Name**: Sales Lead Qualification Workflow
- **Category**: `sales`
- **Type**: Write (`is_write: true`)
- **Primary Webhook Endpoint**: `POST ${N8N_BASE_URL}/webhook/agentx-sales-process-lead`

---

## 4. Request & Response Payload Contracts

### Request Payload (Sent to n8n Webhook)
```json
{
  "task_id": "task_exec_process_lead",
  "agent_id": "sales",
  "workflow_id": "sales_process_lead",
  "lead_id": "LEAD-001",
  "requested_action": "process_lead",
  "name": "Rajesh Khanna",
  "email": "rajesh@cyberdyne.co.in",
  "company": "Cyberdyne Tech",
  "request": "Inquired about 500 seat enterprise expansion",
  "context": {
    "name": "Rajesh Khanna",
    "email": "rajesh@cyberdyne.co.in",
    "company": "Cyberdyne Tech",
    "request": "Inquired about 500 seat enterprise expansion",
    "notes": "Inquired about 500 seat enterprise expansion"
  }
}
```

### Response Contract (Returned by Tool Execution)
```json
{
  "success": true,
  "task_id": "task_exec_process_lead",
  "lead_id": "LEAD-001",
  "activity_created": true,
  "message": "Sales follow-up prepared and activity logged successfully.",
  "lead_status": "qualified",
  "qualification": {
    "score": 88,
    "tier": "TIER_1_ENTERPRISE",
    "status": "qualified"
  },
  "follow_up": {
    "prepared": true,
    "subject": "Tailored Enterprise Proposal for Cyberdyne Tech",
    "message": "Hello Rajesh, regarding your Cyberdyne Tech expansion..."
  }
}
```

---

## 5. Resilience & Timeout Handling

1. **Timeout**: Configured to 10.0 seconds timeout (`N8N_TIMEOUT`).
2. **Connection Error**: Returns structured error `N8N_UNAVAILABLE` when n8n is offline or unreachable.
3. **Fallback Execution**: If n8n connection fails or returns 404, AgentX logs a graceful fallback activity and updates local lead state so task execution completes cleanly without crashing.

---

## 6. Verification with Demo Lead (`LEAD-001`)

To test the integration end-to-end:
1. Ensure n8n is running on `http://localhost:32768`.
2. Dispatch a task: *"Process lead LEAD-001 and draft enterprise proposal."*
3. The Sales Agent routes the task, selects `sales_process_lead`, invokes n8n, synchronizes lead status for `LEAD-001` (Rajesh Khanna / Cyberdyne Tech), and records an auditable activity record.
