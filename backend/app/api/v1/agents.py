from typing import List
from fastapi import APIRouter, HTTPException, status
from app.agents.router import AgentRouter
from app.schemas.agent import AgentResponse

router = APIRouter()
_router_instance = AgentRouter()


@router.get(
    "",
    response_model=List[AgentResponse],
    summary="List all AI teammates and their capabilities",
)
async def list_agents() -> List[AgentResponse]:
    """Return all specialized AI teammates (Support, Sales, Operations) and their capabilities."""
    agents = _router_instance.list_all_agents()
    return [
        AgentResponse(
            agent_id=a.agent_id,
            name=a.name,
            role=a.role,
            description=a.description,
            responsibilities=a.responsibilities,
            capabilities=a.capabilities,
            available_tools=a.available_tools,
        )
        for a in agents
    ]


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Inspect a specific AI teammate",
)
async def get_agent(agent_id: str) -> AgentResponse:
    """Return identity, responsibilities, capabilities, and tools for a specific teammate."""
    agent = _router_instance.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teammate with ID '{agent_id}' not found. Available agents: support, sales, operations",
        )

    return AgentResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        responsibilities=agent.responsibilities,
        capabilities=agent.capabilities,
        available_tools=agent.available_tools,
    )
