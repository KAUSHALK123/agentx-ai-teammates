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
]


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    logger.info("Executing: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = (res.stdout + "\n" + res.stderr).strip()
    return res.returncode, out


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

    # 3. Publish workflows
    code, out = run_cmd(["docker", "exec", "n8n", "n8n", "publish:workflow", "--all"])
    logger.info("Publish output: %s", out)

    # 4. Give n8n a second to register webhooks
    time.sleep(2)

    # 5. Test webhooks
    base_url = "http://localhost:32768"
    client = httpx.Client(timeout=10.0)

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
