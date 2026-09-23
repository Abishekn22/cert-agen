"""Core Certificate Operations AI Agent implementation."""
import json
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.agent.ollama_client import ollama_client, OllamaError
from app.agent.prompts import get_system_prompt, get_synthesis_prompt
from app.agent.tool_registry import tool_registry
from app.schemas.agent import AgentResponse, ToolCallRecord, ActionConfirmation
from app.services.certificate_service import CertificateService
from app.services.renewal_service import RenewalService
from app.utils.logger import logger

class CertificateAgent:
    def __init__(self, client=None, registry=None):
        self.client = client or ollama_client
        self.registry = registry or tool_registry

    async def process_query(self, question: str, db: Session) -> AgentResponse:
        start_time = time.time()
        logger.info(f"Agent processing question: '{question}'")

        system_prompt = get_system_prompt()
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        tools = self.registry.get_ollama_tools()

        try:
            llm_response = await self.client.chat(messages=messages, tools=tools)
        except OllamaError as oe:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                answer=oe.message,
                tool_calls=[],
                execution_time_ms=elapsed_ms,
                records=None,
            )
        except Exception as e:
            logger.error(f"Unexpected agent error in Ollama call: {e}", exc_info=True)
            elapsed_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                answer="An unexpected error occurred while communicating with the AI service. Please verify that Ollama is active.",
                tool_calls=[],
                execution_time_ms=elapsed_ms,
            )

        msg = llm_response.get("message", {})
        raw_tool_calls = msg.get("tool_calls") or []

        tool_records: List[ToolCallRecord] = []
        records_for_ui: Optional[List[Dict[str, Any]]] = None
        action_confirmation: Optional[ActionConfirmation] = None

        if not raw_tool_calls:
            # Model responded directly without calling a tool
            direct_answer = msg.get("content", "").strip() or "No relevant information or tool found for your request."
            elapsed_ms = int((time.time() - start_time) * 1000)
            return AgentResponse(
                answer=direct_answer,
                tool_calls=[],
                execution_time_ms=elapsed_ms,
            )

        # Process each tool call selected by the LLM
        for tc in raw_tool_calls:
            fn = tc.get("function", {})
            tool_name = fn.get("name", "")
            raw_args = fn.get("arguments", {})

            # Ensure arguments is a dict
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {}
            else:
                args = raw_args or {}

            # Check if this tool is an ACTION requiring human-in-the-loop confirmation
            if self.registry.is_action_tool(tool_name):
                cert_id = str(args.get("certificate_id", "")).strip()
                logger.info(f"Action tool '{tool_name}' detected for certificate '{cert_id}'. Requiring confirmation.")

                # Pre-validate before presenting confirmation
                cert = CertificateService.get_by_id(db, cert_id)
                if not cert:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    tool_records.append(
                        ToolCallRecord(
                            tool_name=tool_name,
                            arguments=args,
                            result_summary=f"Certificate {cert_id} was not found.",
                            success=False,
                            error_message=f"Certificate {cert_id} was not found.",
                        )
                    )
                    return AgentResponse(
                        answer=f"Certificate {cert_id} was not found in the operations database.",
                        tool_calls=tool_records,
                        execution_time_ms=elapsed_ms,
                    )

                if cert.revoked or cert.status == "REVOKED":
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    tool_records.append(
                        ToolCallRecord(
                            tool_name=tool_name,
                            arguments=args,
                            result_summary=f"Certificate {cert.certificate_id} is already revoked.",
                            success=False,
                            error_message=f"Certificate {cert.certificate_id} is already revoked.",
                        )
                    )
                    return AgentResponse(
                        answer=f"Certificate {cert.certificate_id} is already revoked and cannot be renewed (Reason: {cert.revocation_reason or 'Revoked'}).",
                        tool_calls=tool_records,
                        execution_time_ms=elapsed_ms,
                    )

                existing_renewal = RenewalService.get_active_renewal_for_cert(db, cert.certificate_id)
                if existing_renewal:
                    elapsed_ms = int((time.time() - start_time) * 1000)
                    tool_records.append(
                        ToolCallRecord(
                            tool_name=tool_name,
                            arguments=args,
                            result_summary=f"Active renewal already exists: {existing_renewal.request_id}",
                            success=False,
                            error_message=f"Active renewal already exists: {existing_renewal.request_id}",
                        )
                    )
                    return AgentResponse(
                        answer=f"An active renewal request already exists for {cert.certificate_id} ({existing_renewal.request_id} with status '{existing_renewal.status}').",
                        tool_calls=tool_records,
                        execution_time_ms=elapsed_ms,
                    )

                # Return confirmation requirement
                action_confirmation = ActionConfirmation(
                    action_type="CREATE_RENEWAL",
                    certificate_id=cert.certificate_id,
                    customer_name=cert.customer_name,
                    description=f"Renewal request will be created for certificate {cert.certificate_id}.",
                )

                tool_records.append(
                    ToolCallRecord(
                        tool_name=tool_name,
                        arguments=args,
                        result_summary=f"Requires user confirmation to create renewal for {cert.certificate_id}",
                        success=True,
                    )
                )

                elapsed_ms = int((time.time() - start_time) * 1000)
                return AgentResponse(
                    answer=f"Renewal request will be created for certificate {cert.certificate_id}. Please review and confirm to proceed.",
                    tool_calls=tool_records,
                    execution_time_ms=elapsed_ms,
                    action_required=action_confirmation,
                    records=[{
                        "certificate_id": cert.certificate_id,
                        "customer_name": cert.customer_name,
                        "domain": cert.domain,
                        "certificate_type": cert.certificate_type,
                        "expires_at": cert.expires_at.isoformat(),
                        "status": cert.status,
                    }],
                )

            # Standard Read-Only Tool Execution
            tool_result = self.registry.execute(tool_name, db=db, arguments=args)
            success = tool_result.get("success", True) if "success" in tool_result else not ("error" in tool_result or tool_result.get("found") is False)

            # Summarize result for observability
            if "summary" in tool_result:
                summary = tool_result["summary"]
            elif tool_result.get("found") is False:
                summary = tool_result.get("message", f"Certificate not found.")
            elif tool_result.get("found") is True:
                summary = f"Found certificate {tool_result.get('certificate_id')} ({tool_result.get('status')})"
            elif "error" in tool_result:
                summary = tool_result["error"]
            else:
                summary = f"Tool {tool_name} executed successfully"

            tool_records.append(
                ToolCallRecord(
                    tool_name=tool_name,
                    arguments=args,
                    result_summary=summary,
                    success=success,
                    error_message=tool_result.get("error") or (tool_result.get("message") if not success else None),
                )
            )

            # Extract records list for frontend tabular view
            if "certificates" in tool_result and isinstance(tool_result["certificates"], list):
                records_for_ui = tool_result["certificates"]
            elif tool_result.get("found") is True:
                records_for_ui = [{
                    "certificate_id": tool_result.get("certificate_id"),
                    "customer_name": tool_result.get("customer_name"),
                    "domain": tool_result.get("domain"),
                    "certificate_type": tool_result.get("certificate_type", "TLS"),
                    "issued_at": tool_result.get("issued_at"),
                    "expires_at": tool_result.get("expires_at"),
                    "status": tool_result.get("status"),
                    "revoked": tool_result.get("revoked", False),
                    "revocation_date": tool_result.get("revocation_date"),
                    "revocation_reason": tool_result.get("revocation_reason"),
                }]

            # Feed tool result back to Ollama to generate final concise answer
            followup_messages = [
                {"role": "system", "content": get_synthesis_prompt(question, tool_name, json.dumps(tool_result))},
                {"role": "user", "content": f"Based on the tool results for '{question}', give the concise operational summary:"},
            ]

            try:
                synthesis_response = await self.client.chat(messages=followup_messages)
                final_answer = synthesis_response.get("message", {}).get("content", "").strip()
            except Exception as e:
                logger.warning(f"Could not generate synthesis answer: {e}. Falling back to tool summary.")
                final_answer = summary

        elapsed_ms = int((time.time() - start_time) * 1000)
        return AgentResponse(
            answer=final_answer or "Operation completed successfully.",
            tool_calls=tool_records,
            execution_time_ms=elapsed_ms,
            records=records_for_ui,
            action_required=action_confirmation,
        )

# Global agent singleton
certificate_agent = CertificateAgent()
