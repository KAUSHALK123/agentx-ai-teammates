import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership, WorkspaceRole, WorkspaceMembershipStatus
from app.models.agent_ownership import (
    AgentInstance,
    AgentMembership,
    AgentMemberRole,
    AgentMembershipStatus,
    AgentInvitation,
    AgentInvitationStatus,
)
from app.models.task import AgentType


class AccessControlStore:
    """Thread-safe in-memory repository managing Workspaces, Users, Agents & Memberships."""

    def __init__(self):
        self._users: Dict[str, User] = {}
        self._workspaces: Dict[str, Workspace] = {}
        # Key: (workspace_id, user_id)
        self._workspace_memberships: Dict[str, WorkspaceMembership] = {}
        # Key: agent_id
        self._agent_instances: Dict[str, AgentInstance] = {}
        # Key: (agent_id, user_id)
        self._agent_memberships: Dict[str, AgentMembership] = {}
        # Key: invitation_id
        self._agent_invitations: Dict[str, AgentInvitation] = {}
        self._lock = asyncio.Lock()
        self._seed_default_data()

    def _seed_default_data(self):
        """Seed initial backward-compatible demo data."""
        # 1. Users
        user_owner = User(
            id="usr_demo_owner",
            email="alex.rivera@acme.com",
            full_name="Alex Rivera",
        )
        user_member = User(
            id="usr_demo_member",
            email="k8849819@gmail.com",
            full_name="Kaushal",
        )
        self._users[user_owner.id] = user_owner
        self._users[user_member.id] = user_member

        # 2. Default Workspace
        ws_default = Workspace(
            id="ws_default",
            name="Acme Corp - Global Operations",
            created_by=user_owner.id,
        )
        self._workspaces[ws_default.id] = ws_default

        # Workspace Memberships
        m1 = WorkspaceMembership(
            workspace_id=ws_default.id,
            user_id=user_owner.id,
            role=WorkspaceRole.OWNER,
            status=WorkspaceMembershipStatus.ACTIVE,
        )
        m2 = WorkspaceMembership(
            workspace_id=ws_default.id,
            user_id=user_member.id,
            role=WorkspaceRole.MEMBER,
            status=WorkspaceMembershipStatus.ACTIVE,
        )
        self._workspace_memberships[f"{ws_default.id}:{user_owner.id}"] = m1
        self._workspace_memberships[f"{ws_default.id}:{user_member.id}"] = m2

        # 3. Default Agent Instances
        agents_data = [
            ("support", "Support Teammate", AgentType.SUPPORT, "Customer Resolution Specialist"),
            ("sales", "Sales Teammate", AgentType.SALES, "Commercial Account & Lead Specialist"),
            ("operations", "Operations Teammate", AgentType.OPERATIONS, "Logistics & Operational Workflow Specialist"),
        ]

        for a_id, name, a_type, desc in agents_data:
            ag = AgentInstance(
                id=a_id,
                workspace_id=ws_default.id,
                owner_id=user_owner.id,
                name=name,
                agent_type=a_type,
                description=desc,
                status="Online",
            )
            self._agent_instances[ag.id] = ag

            # Memberships
            am_owner = AgentMembership(
                agent_id=ag.id,
                user_id=user_owner.id,
                role=AgentMemberRole.OWNER,
                status=AgentMembershipStatus.ACTIVE,
            )
            am_member = AgentMembership(
                agent_id=ag.id,
                user_id=user_member.id,
                role=AgentMemberRole.MEMBER,
                status=AgentMembershipStatus.ACTIVE,
            )
            self._agent_memberships[f"{ag.id}:{user_owner.id}"] = am_owner
            self._agent_memberships[f"{ag.id}:{user_member.id}"] = am_member

    # --- User Methods ---
    async def get_user(self, user_id: str) -> Optional[User]:
        async with self._lock:
            u = self._users.get(user_id)
            return u.model_copy(deep=True) if u else None

    async def save_user(self, user: User) -> User:
        async with self._lock:
            self._users[user.id] = user.model_copy(deep=True)
            return user

    # --- Workspace Methods ---
    async def create_workspace(self, workspace: Workspace) -> Workspace:
        async with self._lock:
            self._workspaces[workspace.id] = workspace.model_copy(deep=True)
            # Automatically add creator as OWNER
            m = WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=workspace.created_by,
                role=WorkspaceRole.OWNER,
                status=WorkspaceMembershipStatus.ACTIVE,
            )
            self._workspace_memberships[f"{workspace.id}:{workspace.created_by}"] = m
            return workspace

    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        async with self._lock:
            ws = self._workspaces.get(workspace_id)
            return ws.model_copy(deep=True) if ws else None

    async def list_user_workspaces(self, user_id: str) -> List[Workspace]:
        async with self._lock:
            res = []
            for key, m in self._workspace_memberships.items():
                if m.user_id == user_id and m.status == WorkspaceMembershipStatus.ACTIVE:
                    ws = self._workspaces.get(m.workspace_id)
                    if ws:
                        res.append(ws.model_copy(deep=True))
            return res

    async def get_workspace_membership(self, workspace_id: str, user_id: str) -> Optional[WorkspaceMembership]:
        async with self._lock:
            m = self._workspace_memberships.get(f"{workspace_id}:{user_id}")
            return m.model_copy(deep=True) if m else None

    async def save_workspace_membership(self, membership: WorkspaceMembership) -> WorkspaceMembership:
        async with self._lock:
            key = f"{membership.workspace_id}:{membership.user_id}"
            self._workspace_memberships[key] = membership.model_copy(deep=True)
            return membership

    async def list_workspace_members(self, workspace_id: str) -> List[WorkspaceMembership]:
        async with self._lock:
            return [
                m.model_copy(deep=True)
                for m in self._workspace_memberships.values()
                if m.workspace_id == workspace_id and m.status == WorkspaceMembershipStatus.ACTIVE
            ]

    # --- Agent Instance Methods ---
    async def create_agent_instance(self, agent: AgentInstance) -> AgentInstance:
        async with self._lock:
            self._agent_instances[agent.id] = agent.model_copy(deep=True)
            # Add creator as OWNER
            am = AgentMembership(
                agent_id=agent.id,
                user_id=agent.owner_id,
                role=AgentMemberRole.OWNER,
                status=AgentMembershipStatus.ACTIVE,
            )
            self._agent_memberships[f"{agent.id}:{agent.owner_id}"] = am
            return agent

    async def get_agent_instance(self, agent_id: str) -> Optional[AgentInstance]:
        async with self._lock:
            ag = self._agent_instances.get(agent_id)
            return ag.model_copy(deep=True) if ag else None

    async def list_workspace_agents(self, workspace_id: str, user_id: Optional[str] = None) -> List[AgentInstance]:
        async with self._lock:
            res = []
            for ag in self._agent_instances.values():
                if ag.workspace_id == workspace_id:
                    if user_id:
                        mem = self._agent_memberships.get(f"{ag.id}:{user_id}")
                        if mem and mem.status == AgentMembershipStatus.ACTIVE:
                            res.append(ag.model_copy(deep=True))
                    else:
                        res.append(ag.model_copy(deep=True))
            return res

    # --- Agent Membership Methods ---
    async def get_agent_membership(self, agent_id: str, user_id: str) -> Optional[AgentMembership]:
        async with self._lock:
            mem = self._agent_memberships.get(f"{agent_id}:{user_id}")
            return mem.model_copy(deep=True) if mem else None

    async def save_agent_membership(self, membership: AgentMembership) -> AgentMembership:
        async with self._lock:
            key = f"{membership.agent_id}:{membership.user_id}"
            self._agent_memberships[key] = membership.model_copy(deep=True)
            return membership

    async def remove_agent_membership(self, agent_id: str, user_id: str) -> bool:
        async with self._lock:
            key = f"{agent_id}:{user_id}"
            if key in self._agent_memberships:
                del self._agent_memberships[key]
                return True
            return False

    async def list_agent_members(self, agent_id: str) -> List[AgentMembership]:
        async with self._lock:
            return [
                m.model_copy(deep=True)
                for m in self._agent_memberships.values()
                if m.agent_id == agent_id and m.status == AgentMembershipStatus.ACTIVE
            ]

    # --- Agent Invitation Methods ---
    async def create_agent_invitation(self, invitation: AgentInvitation) -> AgentInvitation:
        async with self._lock:
            self._agent_invitations[invitation.invitation_id] = invitation.model_copy(deep=True)
            return invitation

    async def get_agent_invitation(self, invitation_id: str) -> Optional[AgentInvitation]:
        async with self._lock:
            inv = self._agent_invitations.get(invitation_id)
            return inv.model_copy(deep=True) if inv else None

    async def update_agent_invitation(self, invitation: AgentInvitation) -> AgentInvitation:
        async with self._lock:
            self._agent_invitations[invitation.invitation_id] = invitation.model_copy(deep=True)
            return invitation

    async def list_pending_invitations_for_user(self, user_id: str, email: Optional[str] = None) -> List[AgentInvitation]:
        async with self._lock:
            res = []
            for inv in self._agent_invitations.values():
                if inv.status == AgentInvitationStatus.PENDING:
                    if inv.user_id == user_id or (email and inv.email and inv.email.lower() == email.lower()):
                        res.append(inv.model_copy(deep=True))
            return res


# Global singleton access control store instance
_global_access_control_store = AccessControlStore()


def get_access_control_store() -> AccessControlStore:
    """Return access control store singleton."""
    return _global_access_control_store
