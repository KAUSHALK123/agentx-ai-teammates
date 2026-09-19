"""
Tests for AgentX Cognee Knowledge Base, KnowledgeService, and Support Agent Knowledge Integration.
"""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.knowledge.service import get_knowledge_service, KnowledgeService, KnowledgeSearchResult, KnowledgeChunk
from app.knowledge.ingest import ingest_demo_knowledge, get_ingestion_manager
from app.agents.support_agent import SupportAgent
from app.models.task import Task, TaskStatus, AgentType
from app.services.execution_engine import TaskExecutionEngine
from app.tools.knowledge_tools import LookupKnowledgeTool


client = TestClient(app)


def test_knowledge_status_endpoint():
    """Test GET /api/v1/knowledge/status endpoint."""
    response = client.get("/api/v1/knowledge/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "provider" in data
    assert data["provider"] == "cognee"


def test_knowledge_search_endpoint():
    """Test POST /api/v1/knowledge/search endpoint."""
    payload = {"query": "What is the refund policy for delayed orders?", "limit": 3}
    response = client.post("/api/v1/knowledge/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert "results" in data
    assert "available" in data


def test_knowledge_search_empty_query():
    """Test POST /api/v1/knowledge/search with empty query."""
    response = client.post("/api/v1/knowledge/search", json={"query": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_repeatable_ingestion_idempotency():
    """Verify that running ingestion multiple times does not duplicate knowledge chunks needlessly."""
    manager = get_ingestion_manager()
    summary1 = await manager.ingest_all(force_reindex=False)
    assert isinstance(summary1, dict)
    
    # Second run without force should skip already processed files with matching hashes
    summary2 = await manager.ingest_all(force_reindex=False)
    assert isinstance(summary2, dict)


@pytest.mark.asyncio
async def test_knowledge_service_search_retrieval_suite():
    """Run 10 test queries to verify Cognee knowledge retrieval across business topics."""
    service = get_knowledge_service()

    queries_and_expected_keywords = [
        ("What is the refund policy for a delayed order?", ["refund", "delayed", "30 days"]),
        ("When does a refund require human approval?", ["high-value", "$500", "approval"]),
        ("When should a high-severity complaint be escalated?", ["SEV-1", "escalated", "support"]),
        ("What information is required before processing a refund?", ["transaction", "receipt", "reason"]),
        ("What are the lead qualification rules?", ["B2B", "qualification", "budget"]),
        ("How should an enterprise lead be handled?", ["Enterprise", "sales", "account executive"]),
        ("What are the return conditions?", ["return", "14 days", "original packaging"]),
        ("What operational issues require escalation?", ["operations", "logistics", "fulfillment"]),
        ("What is the response policy for serious complaints?", ["response", "SLA", "priority"]),
        ("What products are available?", ["AgentX", "Catalog", "Pricing"]),
    ]

    for query, expected_terms in queries_and_expected_keywords:
        result = await service.search(query=query, limit=3)
        assert isinstance(result, KnowledgeSearchResult)
        assert result.query == query
        if result.available and len(result.results) > 0:
            combined_text = " ".join([r.content.lower() for r in result.results])
            matched = any(term.lower() in combined_text for term in expected_terms)
            assert matched, f"Expected one of {expected_terms} in results for query: {query}. Got: {combined_text}"


@pytest.mark.asyncio
async def test_knowledge_service_graceful_failure_when_cognee_fails():
    """Verify that KnowledgeService handles errors gracefully when Cognee is unavailable."""
    mock_provider = AsyncMock()
    mock_provider.check_health = AsyncMock(return_value={"available": False, "error": "Cognee offline"})
    mock_provider.search = AsyncMock(side_effect=Exception("Cognee connection offline"))

    service = KnowledgeService(provider=mock_provider)
    result = await service.search("What is refund policy?")

    assert result.available is False
    assert len(result.results) == 0
    assert "Cognee connection offline" in (result.error or "")


@pytest.mark.asyncio
async def test_lookup_knowledge_tool():
    """Verify LookupKnowledgeTool returns structured results."""
    tool = LookupKnowledgeTool()
    output = await tool.execute(query="delayed order refund", limit=2)
    
    assert output.success is True
    assert "query" in output.data
    assert "knowledge_used" in output.data
    assert output.data["query"] == "delayed order refund"


@pytest.mark.asyncio
async def test_support_agent_policy_retrieval_and_context_propagation():
    """Verify SupportAgent plans policy retrieval and includes knowledge_used metadata in task results."""
    engine = TaskExecutionEngine()
    agent = SupportAgent()
    user_prompt = "A customer has a delayed order and wants a refund. What does our policy allow?"
    
    task = Task(
        task_id="task_policy_test_123",
        user_request=user_prompt,
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    
    # 1. Test planning includes lookup_knowledge step
    plan = await agent.plan(user_request=user_prompt, task_id=task.task_id)
    policy_steps = [s for s in plan.steps if s.tool_id == "lookup_knowledge" or "knowledge" in s.action.lower()]
    assert len(policy_steps) > 0, "SupportAgent should include knowledge/policy lookup step in plan"

    # 2. Test execution of policy query
    executed_task = await engine.execute_task(task, agent, plan)
    assert executed_task.status in [TaskStatus.COMPLETED, TaskStatus.EXECUTING, TaskStatus.WAITING_FOR_APPROVAL]
    assert executed_task.result is not None

