import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.data_service import DemoDataService
from app.services.tool_executor import ToolExecutionService, get_tool_executor
from app.tools.implementations import (
    CreateActivityTool,
    GetBusinessDataTool,
    LookupCustomerTool,
    LookupOrderTool,
    LookupTransactionTool,
    LookupLeadTool,
    UpdateLeadTool,
    VerifyRecordTool,
)
from app.tools.registry import ToolRegistry, get_tool_registry


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def data_service():
    """DemoDataService fixture."""
    return DemoDataService()


# ==========================================
# 1. Tool Registry & Metadata Tests
# ==========================================

def test_tool_registry_registration_and_lookup():
    """Verify tool registration, lookup, and existence check."""
    registry = ToolRegistry()
    tool = LookupCustomerTool()
    registry.register_tool(tool)

    assert registry.has_tool("lookup_customer") is True
    assert registry.has_tool("nonexistent_tool") is False
    assert registry.get_tool("lookup_customer") == tool

    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0].tool_id == "lookup_customer"


def test_tool_read_vs_write_classification():
    """Verify explicit read vs write classification on all tools."""
    registry = get_tool_registry()

    read_tools = [
        "lookup_customer",
        "lookup_order",
        "lookup_transaction",
        "lookup_lead",
        "get_business_data",
        "verify_record",
    ]
    for tid in read_tools:
        tool = registry.get_tool(tid)
        assert tool is not None, f"Tool {tid} not registered"
        assert tool.is_write is False, f"Tool {tid} should be a READ tool"

    write_tools = ["update_lead", "create_activity"]
    for tid in write_tools:
        tool = registry.get_tool(tid)
        assert tool is not None, f"Tool {tid} not registered"
        assert tool.is_write is True, f"Tool {tid} should be a WRITE tool"


# ==========================================
# 2. Individual Tool Execution Tests
# ==========================================

@pytest.mark.asyncio
async def test_lookup_customer_tool(data_service):
    """Test customer lookup by ID and search query."""
    tool = LookupCustomerTool(data_service=data_service)

    # By ID
    res = await tool.execute(customer_id="CUST-001")
    assert res.success is True
    assert res.data["name"] == "Alice Sharma"

    # By Query (email)
    res_email = await tool.execute(query="bob.mehta@example.com")
    assert res_email.success is True
    assert res_email.data["customer_id"] == "CUST-002"

    # Not found
    res_none = await tool.execute(customer_id="CUST-999")
    assert res_none.success is False
    assert "not found" in res_none.error.lower()


@pytest.mark.asyncio
async def test_lookup_order_tool(data_service):
    """Test order lookup by order_id and customer_id."""
    tool = LookupOrderTool(data_service=data_service)

    # By order_id
    res = await tool.execute(order_id="ORD-1001")
    assert res.success is True
    assert res.data["amount"] == 2499.00
    assert res.data["status"] == "delivered"

    # By customer_id
    res_cust = await tool.execute(customer_id="CUST-001")
    assert res_cust.success is True
    assert res_cust.data["count"] >= 2


@pytest.mark.asyncio
async def test_lookup_transaction_tool(data_service):
    """Test transaction lookup by transaction_id and order_id."""
    tool = LookupTransactionTool(data_service=data_service)

    res = await tool.execute(transaction_id="TXN-5001")
    assert res.success is True
    assert res.data["payment_status"] == "successful"

    res_fail = await tool.execute(transaction_id="TXN-9999")
    assert res_fail.success is False


@pytest.mark.asyncio
async def test_lookup_lead_tool(data_service):
    """Test lead lookup by lead_id and company name."""
    tool = LookupLeadTool(data_service=data_service)

    res = await tool.execute(lead_id="LEAD-001")
    assert res.success is True
    assert res.data["company"] == "Cyberdyne Tech"

    res_comp = await tool.execute(query="Wayne")
    assert res_comp.success is True
    assert res_comp.data["lead_id"] == "LEAD-002"


@pytest.mark.asyncio
async def test_update_lead_tool(data_service):
    """Test lead update (WRITE tool)."""
    tool = UpdateLeadTool(data_service=data_service)

    res = await tool.execute(lead_id="LEAD-001", status="qualified", notes="Budget approved")
    assert res.success is True
    assert res.data["status"] == "qualified"

    # Nonexistent lead
    res_missing = await tool.execute(lead_id="LEAD-999", status="lost")
    assert res_missing.success is False


@pytest.mark.asyncio
async def test_get_business_data_tool(data_service):
    """Test operational business data retrieval."""
    tool = GetBusinessDataTool(data_service=data_service)

    res = await tool.execute(metric_type="daily_summary")
    assert res.success is True
    assert "metrics" in res.data
    assert "total_revenue" in res.data["metrics"]


@pytest.mark.asyncio
async def test_verify_record_tool(data_service):
    """Test record verification against expected values."""
    tool = VerifyRecordTool(data_service=data_service)

    # Valid match
    res_match = await tool.execute(
        record_type="order",
        record_id="ORD-1001",
        expected_fields={"status": "delivered", "payment_status": "successful"},
    )
    assert res_match.success is True
    assert res_match.data["matches_expected"] is True

    # Discrepancy detected
    res_disc = await tool.execute(
        record_type="order",
        record_id="ORD-1001",
        expected_fields={"status": "cancelled"},
    )
    assert res_disc.success is True
    assert res_disc.data["matches_expected"] is False
    assert len(res_disc.data["discrepancies"]) > 0


@pytest.mark.asyncio
async def test_create_activity_tool(data_service):
    """Test activity creation (WRITE tool)."""
    tool = CreateActivityTool(data_service=data_service)

    res = await tool.execute(
        task_id="task_123",
        type="note",
        description="Customer requested updated invoice receipt",
    )
    assert res.success is True
    assert res.data["activity_id"].startswith("act_")


# ==========================================
# 3. Tool Execution Service & Permissions
# ==========================================

@pytest.mark.asyncio
async def test_tool_executor_permission_enforcement():
    """Verify tool execution service enforces strict agent-to-tool permissions."""
    executor = ToolExecutionService()

    # 1. Support is allowed to lookup customer
    res_allowed = await executor.execute_tool(
        tool_id="lookup_customer",
        agent_id="support",
        parameters={"customer_id": "CUST-001"},
    )
    assert res_allowed.success is True

    # 2. Support is NOT allowed to update leads (Sales tool)
    res_denied = await executor.execute_tool(
        tool_id="update_lead",
        agent_id="support",
        parameters={"lead_id": "LEAD-001", "status": "qualified"},
    )
    assert res_denied.success is False
    assert "not authorized" in res_denied.error.lower()

    # 3. Sales is allowed to update leads
    res_sales = await executor.execute_tool(
        tool_id="update_lead",
        agent_id="sales",
        parameters={"lead_id": "LEAD-001", "status": "qualified"},
    )
    assert res_sales.success is True

    # 4. Operations is NOT allowed to lookup transactions (Support tool)
    res_ops_denied = await executor.execute_tool(
        tool_id="lookup_transaction",
        agent_id="operations",
        parameters={"transaction_id": "TXN-5001"},
    )
    assert res_ops_denied.success is False
    assert "not authorized" in res_ops_denied.error.lower()


@pytest.mark.asyncio
async def test_tool_executor_audit_logging():
    """Verify execution history records every execution attempt without exposing secrets."""
    executor = ToolExecutionService()

    await executor.execute_tool(
        tool_id="lookup_customer",
        agent_id="support",
        parameters={"customer_id": "CUST-001"},
        task_id="task_audit_test",
    )

    logs = await executor.get_execution_logs(limit=10)
    assert len(logs) > 0
    latest = logs[0]
    assert latest.task_id == "task_audit_test"
    assert latest.tool_id == "lookup_customer"
    assert latest.agent_id == "support"
    assert latest.status == "SUCCESS"


# ==========================================
# 4. API Endpoints Tests
# ==========================================

def test_api_get_tools(client):
    """Verify GET /tools returns all registered tools."""
    response = client.get("/tools")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8

    tool_ids = {t["tool_id"] for t in data}
    expected_ids = {
        "lookup_customer",
        "lookup_order",
        "lookup_transaction",
        "lookup_lead",
        "update_lead",
        "get_business_data",
        "verify_record",
        "create_activity",
    }
    assert expected_ids.issubset(tool_ids)


def test_api_get_tool_by_id(client):
    """Verify GET /tools/{tool_id} returns single tool metadata."""
    response = client.get("/tools/lookup_customer")
    assert response.status_code == 200
    tool = response.json()
    assert tool["tool_id"] == "lookup_customer"
    assert tool["is_write"] is False

    res_not_found = client.get("/tools/fake_nonexistent_tool")
    assert res_not_found.status_code == 404


def test_api_post_tool_execute_authorized(client):
    """Verify POST /tools/{tool_id}/execute allows authorized agent."""
    payload = {
        "agent_id": "support",
        "parameters": {"customer_id": "CUST-001"},
    }
    response = client.post("/tools/lookup_customer/execute", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["tool_id"] == "lookup_customer"
    assert res["data"]["name"] == "Alice Sharma"


def test_api_post_tool_execute_forbidden(client):
    """Verify POST /tools/{tool_id}/execute returns 403 when agent is unauthorized."""
    payload = {
        "agent_id": "support",
        "parameters": {"lead_id": "LEAD-001", "status": "qualified"},
    }
    response = client.post("/tools/update_lead/execute", json=payload)
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()
