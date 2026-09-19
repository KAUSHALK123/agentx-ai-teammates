import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.task import AgentType, TaskStatus


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def test_startup_and_health(client):
    """Verify FastAPI application starts and health endpoint responds."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data


def test_root_endpoint(client):
    """Verify landing endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "docs_url" in data


def test_explicit_agent_selection_support(client):
    """Verify explicit selection of Support teammate."""
    payload = {
        "user_request": "Customer order delay inquiry",
        "selected_agent": "support",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["task_id"].startswith("task_")
    assert data["selected_agent"] == AgentType.SUPPORT.value
    assert data["status"] in [TaskStatus.COMPLETED.value, TaskStatus.ESCALATED.value, TaskStatus.WAITING_FOR_APPROVAL.value, TaskStatus.EXECUTING.value, TaskStatus.FAILED.value]


def test_explicit_agent_selection_sales(client):
    """Verify explicit selection of Sales teammate."""
    payload = {
        "user_request": "Request enterprise deal terms",
        "selected_agent": "sales",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_agent"] == AgentType.SALES.value


def test_explicit_agent_selection_operations(client):
    """Verify explicit selection of Operations teammate."""
    payload = {
        "user_request": "Check warehouse inventory levels",
        "selected_agent": "operations",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_agent"] == AgentType.OPERATIONS.value


def test_automatic_agent_routing_sales(client):
    """Verify automatic routing routes pricing/quotes to sales teammate."""
    payload = {
        "user_request": "We need custom pricing and enterprise volume discount for 500 seats",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_agent"] == AgentType.SALES.value


def test_automatic_agent_routing_operations(client):
    """Verify automatic routing routes stock/warehouse queries to operations teammate."""
    payload = {
        "user_request": "Check warehouse stock and inventory for SKU-101 fulfillment",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_agent"] == AgentType.OPERATIONS.value


def test_automatic_agent_routing_support(client):
    """Verify automatic routing defaults to support for customer problems."""
    payload = {
        "user_request": "Customer needs refund and update on delayed ticket #1234",
    }
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["selected_agent"] == AgentType.SUPPORT.value


def test_task_retrieval_by_id(client):
    """Verify full task retrieval by ID including result and execution events."""
    create_res = client.post("/tasks", json={"user_request": "Query ticket #1234 details"})
    assert create_res.status_code == 201
    task_id = create_res.json()["task_id"]

    get_res = client.get(f"/tasks/{task_id}")
    assert get_res.status_code == 200
    task = get_res.json()
    assert task["task_id"] == task_id
    assert task["status"] in [TaskStatus.COMPLETED.value, TaskStatus.ESCALATED.value, TaskStatus.WAITING_FOR_APPROVAL.value, TaskStatus.EXECUTING.value, TaskStatus.FAILED.value]
    assert task["result"] is not None
    assert len(task["events"]) > 0

    # Ensure events do not leak private chain of thought
    for event in task["events"]:
        assert "current_stage" in event
        assert "action_performed" in event
        assert "status" in event
        # Confirm no raw thought dumps
        assert "chain_of_thought" not in event


def test_task_not_found(client):
    """Verify 404 response for nonexistent task ID."""
    response = client.get("/tasks/task_does_not_exist_999")
    assert response.status_code == 404
