"""Unit tests for tool registry and safe tool execution."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.agent.tool_registry import ToolRegistry, tool_registry

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_tool_registry_contains_required_tools():
    required_tools = [
        "get_certificate",
        "get_expiring_certificates",
        "get_certificates_expiring_between",
        "check_revocation",
        "get_customer_certificates",
        "create_renewal_request",
    ]
    for tool_name in required_tools:
        tool = tool_registry.get_tool(tool_name)
        assert tool is not None, f"Tool {tool_name} must be registered."
        assert tool.name == tool_name
        assert len(tool.description) > 10

def test_ollama_tool_schemas():
    ollama_tools = tool_registry.get_ollama_tools()
    assert len(ollama_tools) >= 5
    for item in ollama_tools:
        assert item["type"] == "function"
        fn = item["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn
        assert fn["parameters"]["type"] == "object"

def test_reject_unregistered_tool(db_session):
    result = tool_registry.execute("arbitrary_sql_injection", db=db_session, arguments={"sql": "DROP TABLE certificates"})
    assert result["success"] is False
    assert "not an approved operations tool" in result["error"]

def test_action_tool_flag():
    assert tool_registry.is_action_tool("create_renewal_request") is True
    assert tool_registry.is_action_tool("get_certificate") is False
    assert tool_registry.is_action_tool("get_expiring_certificates") is False
