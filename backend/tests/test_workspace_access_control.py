import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.task import AgentType
from app.models.workspace import WorkspaceRole
from app.models.agent_ownership import AgentMemberRole
from app.services.access_control_store import get_access_control_store

client = TestClient(app)


def test_user_can_access_their_workspace():
    """1. User can access their authorized workspace."""
    headers = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    response = client.get("/workspaces/ws_default", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ws_default"
    assert data["role"] == "OWNER"


def test_user_cannot_access_unauthorized_workspace():
    """2. User cannot access another workspace where they are not a member."""
    # Create isolated workspace for owner
    headers_owner = {"X-User-ID": "usr_owner_A", "X-Workspace-ID": "ws_default"}
    create_res = client.post("/workspaces", json={"name": "Workspace A"}, headers=headers_owner)
    assert create_res.status_code == 201
    ws_id = create_res.json()["id"]

    # Unauthorized user B attempts access
    headers_user_B = {"X-User-ID": "usr_user_B", "X-Workspace-ID": ws_id}
    response = client.get(f"/workspaces/{ws_id}", headers=headers_user_B)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_agent_owner_can_manage_agent_members():
    """3. Agent owner can invite and manage agent members."""
    headers_owner = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    
    # Create custom agent
    ag_res = client.post("/agents", json={
        "name": "Custom Support Agent",
        "agent_type": "support",
        "description": "Specialized tier 2 support agent"
    }, headers=headers_owner)
    assert ag_res.status_code == 201
    ag_id = ag_res.json()["id"]

    # Invite user B as MEMBER
    invite_res = client.post(f"/agents/{ag_id}/members/invite", json={
        "user_id": "usr_user_B",
        "role": "MEMBER"
    }, headers=headers_owner)
    assert invite_res.status_code == 201
    inv_data = invite_res.json()
    assert inv_data["status"] == "PENDING"


def test_pending_invitation_gives_no_access():
    """6. Pending invitation does not grant agent access until accepted."""
    headers_owner = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    
    ag_res = client.post("/agents", json={
        "name": "Private Sales Agent",
        "agent_type": "sales",
        "description": "Private deal closer"
    }, headers=headers_owner)
    ag_id = ag_res.json()["id"]

    # Invite user B
    client.post(f"/agents/{ag_id}/members/invite", json={
        "user_id": "usr_user_B",
        "role": "MEMBER"
    }, headers=headers_owner)

    # User B attempts to access agent before accepting
    headers_user_B = {"X-User-ID": "usr_user_B", "X-Workspace-ID": "ws_default"}
    res = client.get(f"/agents/{ag_id}", headers=headers_user_B)
    assert res.status_code == 403


def test_accepted_invitation_gives_access():
    """7. Accepting invitation grants active member access."""
    headers_owner = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    
    ag_res = client.post("/agents", json={
        "name": "Shared Operations Agent",
        "agent_type": "operations",
        "description": "Shared ops helper"
    }, headers=headers_owner)
    ag_id = ag_res.json()["id"]

    # Invite user B
    inv_res = client.post(f"/agents/{ag_id}/members/invite", json={
        "user_id": "usr_user_B",
        "role": "MEMBER"
    }, headers=headers_owner)
    inv_id = inv_res.json()["invitation_id"]

    # User B accepts invitation
    headers_user_B = {"X-User-ID": "usr_user_B", "X-Workspace-ID": "ws_default"}
    accept_res = client.post(f"/agents/invitations/{inv_id}/accept", headers=headers_user_B)
    assert accept_res.status_code == 200

    # User B can now inspect agent details
    ag_get = client.get(f"/agents/{ag_id}", headers=headers_user_B)
    assert ag_get.status_code == 200
    assert ag_get.json()["agent_id"] == ag_id


def test_revoked_member_loses_access():
    """8. Revoking an agent membership immediately cuts off access."""
    headers_owner = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    
    ag_res = client.post("/agents", json={
        "name": "Temporary Agent",
        "agent_type": "support",
        "description": "Temp agent"
    }, headers=headers_owner)
    ag_id = ag_res.json()["id"]

    # Invite & accept
    inv_res = client.post(f"/agents/{ag_id}/members/invite", json={"user_id": "usr_temp_user", "role": "MEMBER"}, headers=headers_owner)
    inv_id = inv_res.json()["invitation_id"]
    client.post(f"/agents/invitations/{inv_id}/accept", headers={"X-User-ID": "usr_temp_user", "X-Workspace-ID": "ws_default"})

    # Revoke access
    del_res = client.delete(f"/agents/{ag_id}/members/usr_temp_user", headers=headers_owner)
    assert del_res.status_code == 204

    # Temp user loses access
    get_res = client.get(f"/agents/{ag_id}", headers={"X-User-ID": "usr_temp_user", "X-Workspace-ID": "ws_default"})
    assert get_res.status_code == 403


def test_user_cannot_access_another_users_task():
    """9 & 12. User cannot inspect or execute another user's task in an isolated workspace."""
    headers_user_A = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    task_res = client.post("/tasks", json={
        "user_request": "Investigate order ORD-8821",
        "selected_agent": "support"
    }, headers=headers_user_A)
    assert task_res.status_code == 201
    task_id = task_res.json()["task_id"]

    # User C in another workspace attempts IDOR access
    headers_user_C = {"X-User-ID": "usr_user_C", "X-Workspace-ID": "ws_isolated_C"}
    
    # Create isolated workspace for C
    client.post("/workspaces", json={"name": "Workspace C"}, headers=headers_user_C)
    
    get_res = client.get(f"/tasks/{task_id}", headers=headers_user_C)
    assert get_res.status_code in [403, 404]


def test_two_users_run_separate_tasks_simultaneously():
    """10. Two users can execute separate tasks simultaneously without state leakage."""
    headers_user_1 = {"X-User-ID": "usr_demo_owner", "X-Workspace-ID": "ws_default"}
    headers_user_2 = {"X-User-ID": "usr_demo_member", "X-Workspace-ID": "ws_default"}

    t1_res = client.post("/tasks", json={"user_request": "Task 1 customer complaint", "selected_agent": "support"}, headers=headers_user_1)
    t2_res = client.post("/tasks", json={"user_request": "Task 2 lead evaluation", "selected_agent": "sales"}, headers=headers_user_2)

    assert t1_res.status_code == 201
    assert t2_res.status_code == 201

    t1_id = t1_res.json()["task_id"]
    t2_id = t2_res.json()["task_id"]

    assert t1_id != t2_id

    # Verify both tasks exist independently
    get_t1 = client.get(f"/tasks/{t1_id}", headers=headers_user_1)
    get_t2 = client.get(f"/tasks/{t2_id}", headers=headers_user_2)

    assert get_t1.status_code == 200
    assert get_t2.status_code == 200
    assert get_t1.json()["task_id"] == t1_id
    assert get_t2.json()["task_id"] == t2_id
