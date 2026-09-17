import pytest
from fastapi.testclient import TestClient
from app.agents.router import AgentRouter
from app.agents.support_agent import SupportAgent
from app.agents.sales_agent import SalesAgent
from app.agents.operations_agent import OperationsAgent
from app.core.llm import BaseLLMProvider, MockLLMProvider
from app.main import app
from app.services.planner import AIPlanner


@pytest.fixture
def client():
    """Create test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def test_agents_load_and_metadata():
    """Verify all three agents load correctly with expected identity metadata."""
    router = AgentRouter()
    agents = router.list_all_agents()
    assert len(agents) == 3

    agent_ids = {a.agent_id for a in agents}
    assert agent_ids == {"support", "sales", "operations"}

    support = router.get_agent_by_id("support")
    assert isinstance(support, SupportAgent)
    assert support.name == "Support Teammate"
    assert "complaints" in support.responsibilities
    assert "order/payment issue investigation" in support.responsibilities

    sales = router.get_agent_by_id("sales")
    assert isinstance(sales, SalesAgent)
    assert sales.name == "Sales Teammate"
    assert "lead qualification" in sales.responsibilities

    operations = router.get_agent_by_id("operations")
    assert isinstance(operations, OperationsAgent)
    assert operations.name == "Operations Teammate"
    assert "reports" in operations.responsibilities


def test_agent_capabilities_structure():
    """Verify machine-readable capabilities on each agent."""
    router = AgentRouter()
    support = router.get_agent_by_id("support")
    support_caps = [c.name for c in support.capabilities]
    expected_support_caps = [
        "investigate_customer_issue",
        "analyze_complaint",
        "identify_resolution",
        "prepare_response",
        "escalate_issue",
    ]
    for cap in expected_support_caps:
        assert cap in support_caps

    sales = router.get_agent_by_id("sales")
    sales_caps = [c.name for c in sales.capabilities]
    expected_sales_caps = [
        "qualify_lead",
        "analyze_lead",
        "prepare_followup",
        "recommend_next_action",
    ]
    for cap in expected_sales_caps:
        assert cap in sales_caps

    operations = router.get_agent_by_id("operations")
    ops_caps = [c.name for c in operations.capabilities]
    expected_ops_caps = [
        "analyze_business_data",
        "generate_report",
        "verify_records",
        "identify_exception",
        "prepare_operational_action",
    ]
    for cap in expected_ops_caps:
        assert cap in ops_caps


@pytest.mark.asyncio
async def test_support_structured_planning():
    """Verify Support Teammate generates a structured task plan with actionable steps."""
    support = SupportAgent()
    request = "Customer says their payment was successful but their order wasn't confirmed."
    plan = await support.plan(request)

    assert plan.agent == "support"
    assert plan.task_id is not None
    assert len(plan.steps) >= 3
    assert plan.objective is not None
    
    types = [s.type for s in plan.steps]
    assert any(t in types for t in ["investigation", "tool_action", "verification"])


@pytest.mark.asyncio
async def test_sales_structured_planning():
    """Verify Sales Teammate generates a structured task plan."""
    sales = SalesAgent()
    request = "Process this new lead and prepare a personalized follow-up."
    plan = await sales.plan(request)

    assert plan.agent == "sales"
    assert len(plan.steps) >= 3
    assert any(s.type in ["qualification", "investigation", "tool_action"] for s in plan.steps)


@pytest.mark.asyncio
async def test_operations_structured_planning():
    """Verify Operations Teammate generates a structured task plan."""
    operations = OperationsAgent()
    request = "Analyze today's sales data and identify anything that requires attention."
    plan = await operations.plan(request)

    assert plan.agent == "operations"
    assert len(plan.steps) >= 3
    assert any(s.type in ["analysis", "investigation", "tool_action", "verification"] for s in plan.steps)


@pytest.mark.asyncio
async def test_automatic_routing_and_ambiguity():
    """Verify router identifies ambiguous requests and produces RouteResult."""
    router = AgentRouter()

    # Ambiguous / vague request
    ambig_res = await router.determine_route("asdf")
    assert ambig_res.is_ambiguous is True
    assert ambig_res.clarification_prompt is not None

    # Clear support request
    support_res = await router.determine_route("Customer asking for refund on delayed shipment")
    assert support_res.is_ambiguous is False
    assert support_res.selected_agent.value == "support"
    assert support_res.confidence > 0.5
    assert support_res.explanation != ""

    # Clear sales request
    sales_res = await router.determine_route("Enterprise pricing quote for 1000 users")
    assert sales_res.is_ambiguous is False
    assert sales_res.selected_agent.value == "sales"

    # Clear operations request
    ops_res = await router.determine_route("Generate warehouse inventory audit and stock report")
    assert ops_res.is_ambiguous is False
    assert ops_res.selected_agent.value == "operations"


@pytest.mark.asyncio
async def test_explicit_agent_selection():
    """Verify explicit selection is respected."""
    router = AgentRouter()
    res = await router.determine_route("Generic inquiry", explicit_agent="sales")
    assert res.selected_agent.value == "sales"
    assert res.confidence == 1.0


@pytest.mark.asyncio
async def test_planner_malformed_llm_output_resilience():
    """Verify that malformed or non-JSON LLM responses do not crash the planner."""
    # LLM returning corrupted text / code
    bad_llm = MockLLMProvider(preset_response="This is not valid JSON at all! ``` broken { [")
    planner = AIPlanner(llm_provider=bad_llm)
    
    plan = await planner.generate_plan(
        user_request="Handle customer return request",
        agent_id="support",
        agent_name="Support Teammate",
        system_instructions="",
        capabilities=["investigate_customer_issue"],
        available_tools=["ticket_lookup"],
    )

    # Should safely return fallback structured plan
    assert plan is not None
    assert plan.agent == "support"
    assert len(plan.steps) >= 3
    assert plan.steps[0].action != ""


@pytest.mark.asyncio
async def test_planner_llm_exception_resilience():
    """Verify planner survives runtime exceptions from LLM provider."""
    class FailingLLM(BaseLLMProvider):
        async def generate_text(self, prompt: str, system_instruction=None) -> str:
            raise RuntimeError("API Timeout / Out of Quota")

    planner = AIPlanner(llm_provider=FailingLLM())
    plan = await planner.generate_plan(
        user_request="Analyze stock anomaly",
        agent_id="operations",
        agent_name="Operations Teammate",
        system_instructions="",
        capabilities=["identify_exception"],
        available_tools=["inventory_status"],
    )

    assert plan is not None
    assert plan.agent == "operations"
    assert len(plan.steps) >= 3


def test_api_get_agents(client):
    """Verify GET /agents returns all 3 teammates with capabilities."""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    ids = {a["agent_id"] for a in data}
    assert ids == {"support", "sales", "operations"}
    for a in data:
        assert len(a["capabilities"]) > 0
        assert len(a["responsibilities"]) > 0


def test_api_get_individual_agent(client):
    """Verify GET /agents/{agent_id} returns detailed teammate specs."""
    for agent_id in ["support", "sales", "operations"]:
        response = client.get(f"/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
        assert "capabilities" in data


def test_api_get_invalid_agent(client):
    """Verify GET /agents/invalid returns 404."""
    response = client.get("/agents/nonexistent_agent_xyz")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_post_tasks_plan(client):
    """Verify POST /tasks/plan endpoint generates a structured task plan."""
    payload = {
        "user_request": "Customer says their payment was successful but their order wasn't confirmed.",
    }
    response = client.post("/tasks/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_agent"] == "support"
    assert "plan" in data
    assert len(data["plan"]["steps"]) >= 3
    assert data["confidence"] > 0.5


def test_api_post_tasks_plan_explicit(client):
    """Verify POST /tasks/plan with explicit agent override."""
    payload = {
        "user_request": "Prepare market expansion report",
        "selected_agent": "operations",
    }
    response = client.post("/tasks/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_agent"] == "operations"


def test_api_post_tasks_plan_ambiguous(client):
    """Verify POST /tasks/plan with ambiguous input returns clarification state."""
    payload = {
        "user_request": "asdf",
    }
    response = client.post("/tasks/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_ambiguous"] is True
    assert data["clarification_prompt"] is not None


def test_api_post_tasks_plan_empty(client):
    """Verify POST /tasks/plan with whitespace/empty request returns 422."""
    payload = {
        "user_request": "   ",
    }
    response = client.post("/tasks/plan", json=payload)
    assert response.status_code == 422
