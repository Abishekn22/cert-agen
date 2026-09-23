"""Ollama HTTP client for local LLM inference and tool calling."""
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings
from app.utils.logger import logger

class OllamaError(Exception):
    """Base exception for Ollama communication errors."""
    def __init__(self, message: str, status_code: int = 503):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def check_health(self) -> Dict[str, Any]:
        """Verify Ollama server connection and check if configured model is available."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_available = any(
                        self.model == m or self.model in m or m.startswith(self.model.split(":")[0])
                        for m in models
                    )
                    return {
                        "available": True,
                        "status": "connected",
                        "configured_model": self.model,
                        "model_ready": model_available,
                        "installed_models": models,
                    }
                return {
                    "available": False,
                    "status": f"Ollama returned HTTP {res.status_code}",
                    "configured_model": self.model,
                    "model_ready": False,
                }
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return {
                "available": False,
                "status": f"Cannot connect to Ollama at {self.base_url}: {str(e)}",
                "configured_model": self.model,
                "model_ready": False,
            }

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Send chat prompt to Ollama with optional function calling tools.
        """
        url = f"{self.base_url}/api/chat"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Zero temperature for deterministic, factual outputs
            },
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"Dispatching query to Ollama ({self.model}) at {url}")
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    err_msg = f"Ollama returned HTTP {res.status_code}: {res.text}"
                    logger.error(err_msg)
                    raise OllamaError(err_msg, status_code=res.status_code)
                return res.json()
        except httpx.ConnectError as ce:
            logger.error(f"Cannot connect to Ollama server at {self.base_url}: {ce}")
            raise OllamaError("AI service is unavailable. Please ensure Ollama is running.")
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {self.timeout.read}s")
            raise OllamaError("AI service request timed out. The local model may be loading or under heavy load.")
        except OllamaError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error communicating with Ollama: {e}")
            raise OllamaError(f"AI service error: {str(e)}")

ollama_client = OllamaClient()
