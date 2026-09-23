"""Tool Registry managing registered tools, schemas, and safe execution."""
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy.orm import Session
from app.tools.certificate_tools import (
    get_certificate_tool,
    get_expiring_certificates_tool,
    get_certificates_expiring_between_tool,
    check_revocation_tool,
    get_customer_certificates_tool,
)
from app.tools.renewal_tools import create_renewal_request_tool
from app.utils.logger import logger

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable[..., Any],
        is_action: bool = False,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
        self.is_action = is_action

    def to_ollama_tool(self) -> Dict[str, Any]:
        """Convert definition into Ollama function calling tool schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def is_action_tool(self, name: str) -> bool:
        tool = self._tools.get(name)
        return tool.is_action if tool else False

    def get_ollama_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_ollama_tool() for tool in self._tools.values()]

    def execute(self, tool_name: str, db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Safely execute an approved tool. Never executes arbitrary code or SQL."""
        tool = self._tools.get(tool_name)
        if not tool:
            logger.error(f"Attempted execution of unregistered tool: {tool_name}")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' is not an approved operations tool.",
                "tool_name": tool_name,
            }

        try:
            logger.info(f"Dispatching tool '{tool_name}' with arguments: {arguments}")
            result = tool.func(db=db, **arguments)
            return result
        except TypeError as te:
            logger.warning(f"Argument mismatch for tool '{tool_name}': {te}")
            return {
                "success": False,
                "error": f"Invalid arguments provided for tool '{tool_name}': {str(te)}",
                "tool_name": tool_name,
            }
        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution error in tool '{tool_name}': {str(e)}",
                "tool_name": tool_name,
            }

    def _register_default_tools(self):
        # Tool 1: get_certificate
        self.register(
            ToolDefinition(
                name="get_certificate",
                description="Retrieve complete operational information about a specific digital certificate by certificate ID (e.g. ABC123).",
                parameters={
                    "type": "object",
                    "properties": {
                        "certificate_id": {
                            "type": "string",
                            "description": "The unique certificate identifier, such as 'ABC123' or 'XYZ789'.",
                        }
                    },
                    "required": ["certificate_id"],
                },
                func=get_certificate_tool,
                is_action=False,
            )
        )

        # Tool 2: get_expiring_certificates
        self.register(
            ToolDefinition(
                name="get_expiring_certificates",
                description="Return active digital certificates expiring within a specified number of days from today (default 30 days).",
                parameters={
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days from today to check expiration (e.g. 30, 60, 90).",
                        }
                    },
                    "required": ["days"],
                },
                func=get_expiring_certificates_tool,
                is_action=False,
            )
        )

        # Tool 2b: get_certificates_expiring_between
        self.register(
            ToolDefinition(
                name="get_certificates_expiring_between",
                description="Return active digital certificates expiring within a specific calendar date range (e.g. next calendar month). Dates must be in YYYY-MM-DD format.",
                parameters={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format.",
                        },
                    },
                    "required": ["start_date", "end_date"],
                },
                func=get_certificates_expiring_between_tool,
                is_action=False,
            )
        )

        # Tool 3: check_revocation
        self.register(
            ToolDefinition(
                name="check_revocation",
                description="Check whether a digital certificate is revoked, along with revocation date and revocation reason.",
                parameters={
                    "type": "object",
                    "properties": {
                        "certificate_id": {
                            "type": "string",
                            "description": "The unique certificate identifier, such as 'XYZ789'.",
                        }
                    },
                    "required": ["certificate_id"],
                },
                func=check_revocation_tool,
                is_action=False,
            )
        )

        # Tool 4: get_customer_certificates
        self.register(
            ToolDefinition(
                name="get_customer_certificates",
                description="Return all digital certificates belonging to a specific customer or tenant (e.g. 'Customer A').",
                parameters={
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "The exact or partial name of the customer, such as 'Customer A' or 'Customer B'.",
                        }
                    },
                    "required": ["customer_name"],
                },
                func=get_customer_certificates_tool,
                is_action=False,
            )
        )

        # Tool 5: create_renewal_request (Action Tool)
        self.register(
            ToolDefinition(
                name="create_renewal_request",
                description="ACTION TOOL: Generate a renewal request for a digital certificate. Validates certificate exists, is not revoked, and is not already pending renewal.",
                parameters={
                    "type": "object",
                    "properties": {
                        "certificate_id": {
                            "type": "string",
                            "description": "The certificate ID to create a renewal request for (e.g. 'ABC123').",
                        }
                    },
                    "required": ["certificate_id"],
                },
                func=create_renewal_request_tool,
                is_action=True,
            )
        )

# Global registry singleton
tool_registry = ToolRegistry()
