import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app


@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    """
    return TestClient(app)


@pytest.fixture
def mock_agent_invoke():
    """
    Mock the AgentGraphRAGBedRock.invoke method.
    """
    with patch("core.agent.AgentGraphRAGBedRock.invoke", new_callable=AsyncMock) as mock:
        mock.return_value = "This is a test response"
        yield mock


@pytest.fixture
def mock_aupload_knowledge_base():
    """
    Mock the aupload_knowledge_base function.
    """
    with patch("workers.tasks.aupload_knowledge_base", new_callable=AsyncMock) as mock:
        mock.return_value = "test-job-id"
        yield mock