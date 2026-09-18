import json
import logging
import subprocess
import sys
import time
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("setup_n8n")

WORKFLOWS = [
    {
        "file": "d:/PROJECTS/paytm-agent/agentx-ai-teammates/backend/workflows/sales_process_lead.json",
        "container_path": "/home/node/sales_process_lead.json",
        "webhook_path": "agentx-sales-process-lead",
        "test_payload": {
            "task_id": "test-task-1",
            "agent_id": "sales",
            "workflow_id": "sales_process_lead",
            "lead_id": "LEAD-001",
            "requested_action": "process_lead",
            "context": {
                "name": "Rajesh Khanna",
                "email": "rajesh@cyberdyne.co.in",
                "company": "Cyberdyne Tech",
                "source": "inbound_enterprise",
                "notes": "Inquired about 500 seat enterprise expansion",
            },
        },
    },
    {
        "file": "d:/PROJECTS/paytm-agent/agentx-ai-teammates/backend/workflows/sales_send_followup.json",
        "container_path": "/home/node/sales_send_followup.json",
        "webhook_path": "agentx-sales-send-followup",
        "test_payload": {
            "task_id": "test-task-2",
            "agent_id": "sales",
            "workflow_id": "sales_send_followup",
            "lead_id": "LEAD-001",
            "requested_action": "send_followup",
            "follow_up": {
                "recipient_name": "Rajesh Khanna",
                "recipient_email": "rajesh@cyberdyne.co.in",
                "subject": "Enterprise Expansion Proposal",
                "message": "Hello Rajesh...",
            },
        },
    },
    {
        "file": "d:/PROJECTS/paytm-agent/agentx-ai-teammates/backend/workflows/operations_daily_business_check.json",
        "container_path": "/home/node/operations_daily_business_check.json",
        "webhook_path": "agentx-operations-daily-check",
        "test_payload": {
            "task_id": "test-task-ops",
            "agent_id": "operations",
            "workflow_id": "operations_daily_business_check",
            "requested_action": "daily_business_check",
            "context": {"category": "daily_audit"},
        },
    },
]


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    logger.info("Executing: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = (res.stdout + "\n" + res.stderr).strip()
    return res.returncode, out


def get_active_n8n_port() -> int:
    """Detect dynamic mapped port from Docker container."""
    code, out = run_cmd(["docker", "port", "n8n", "5678"])
    if code == 0 and ":" in out:
        for line in out.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 2 and parts[-1].isdigit():
                return int(parts[-1])
    return 32768


def setup():
    logger.info("Starting n8n workflow deployment into container 'n8n'...")

    for wf in WORKFLOWS:
        # 1. Copy workflow file to container
        code, out = run_cmd(["docker", "cp", wf["file"], f"n8n:{wf['container_path']}"])
        if code != 0:
            logger.error("Failed to copy %s: %s", wf["file"], out)
            sys.exit(1)
        logger.info("Copied %s into container", wf["container_path"])

        # 2. Import workflow
        code, out = run_cmd(["docker", "exec", "n8n", "n8n", "import:workflow", f"--input={wf['container_path']}"])
        logger.info("Import output: %s", out)

    # 3. List workflows and publish each by ID
    code, out = run_cmd(["docker", "exec", "n8n", "n8n", "list:workflow"])
    logger.info("Workflow list:\n%s", out)
    if code == 0:
        for line in out.splitlines():
            if "|" in line and "AgentX" in line:
                wf_id = line.split("|")[0].strip()
                logger.info("Publishing workflow: %s", wf_id)
                run_cmd(["docker", "exec", "n8n", "n8n", "publish:workflow", f"--id={wf_id}"])

    # 4. Restart container so webhooks are active
    logger.info("Restarting n8n container to bind published webhooks...")
    run_cmd(["docker", "restart", "n8n"])
    
    port = get_active_n8n_port()
    base_url = f"http://localhost:{port}"
    logger.info("Waiting for n8n instance at %s to be ready...", base_url)

    client = httpx.Client(timeout=10.0)
    for _ in range(15):
        time.sleep(1)
        try:
            r = client.get(f"{base_url}/healthz")
            if r.status_code == 200:
                logger.info("n8n is ready on %s", base_url)
                break
        except Exception:
            pass

    for wf in WORKFLOWS:
        url = f"{base_url}/webhook/{wf['webhook_path']}"
        logger.info("Testing webhook: %s", url)
        try:
            res = client.post(url, json=wf["test_payload"])
            logger.info("Status: %d, Response: %s", res.status_code, res.text[:300])
            if res.status_code == 200:
                logger.info("SUCCESS: Webhook %s is LIVE and operational!", wf["webhook_path"])
            else:
                logger.warning("Webhook returned %d: %s", res.status_code, res.text)
        except Exception as exc:
            logger.error("Failed to call webhook %s: %s", url, exc)


if __name__ == "__main__":
    setup()
