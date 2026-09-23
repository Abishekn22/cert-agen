"""Agent Pydantic schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language question or command")

class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result_summary: str
    success: bool = True
    error_message: Optional[str] = None

class ActionConfirmation(BaseModel):
    action_type: str = Field(..., description="e.g. CREATE_RENEWAL")
    certificate_id: str
    customer_name: Optional[str] = None
    description: str

class AgentResponse(BaseModel):
    answer: str
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    execution_time_ms: int
    action_required: Optional[ActionConfirmation] = None
    records: Optional[List[Dict[str, Any]]] = None
