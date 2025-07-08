from fastapi.testclient import TestClient


def test_root_endpoint(test_client: TestClient):
    """
    Test the root endpoint returns a 200 status code and HTML content.
    """
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_chat_endpoint(test_client: TestClient, mock_agent_invoke):
    """
    Test the chat endpoint with a mocked agent.invoke method.
    """
    chat_id = "test-chat-id"
    request_data = {"question": "What is GraphRAG?"}
    
    response = test_client.post(f"/chat/{chat_id}", json=request_data)
    
    assert response.status_code == 200
    assert response.json() == {"result": "This is a test response"}
    mock_agent_invoke.assert_called_once_with("What is GraphRAG?")


def test_knowledge_update_no_files(test_client: TestClient):
    """
    Test the knowledge update endpoint with no files.
    """
    response = test_client.post("/knowledge/update", files={})
    
    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "No files uploaded.",
        "job_ids": []
    }


def test_knowledge_update_unsupported_file_type(test_client: TestClient):
    """
    Test the knowledge update endpoint with an unsupported file type.
    """
    files = {"files": ("test.exe", b"test content", "application/octet-stream")}
    
    response = test_client.post("/knowledge/update", files=files)
    
    assert response.status_code == 200
    assert response.json() == {
        "success": False,
        "message": "Unsupported file type. Only PDF, TXT, and MD files are allowed.",
        "job_ids": []
    }


def test_knowledge_update_success(test_client: TestClient, mock_aupload_knowledge_base):
    """
    Test the knowledge update endpoint with a valid file.
    """
    files = {"files": ("test.pdf", b"test content", "application/pdf")}
    
    response = test_client.post("/knowledge/update", files=files)
    
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Knowledge base updated successfully.",
        "job_ids": ["test-job-id"]
    }
    mock_aupload_knowledge_base.assert_called_once()