from __future__ import annotations
from typing import Any, Dict, List, Optional
import os, json, httpx

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

class LLMService:
    def __init__(self, base_url=DEFAULT_OLLAMA_URL, model=DEFAULT_MODEL, temperature=0.0, timeout=120.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    async def _chat(self, messages: List[Dict[str, str]], *, json_mode=False, model: Optional[str]=None) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.temperature, **({"format":"json"} if json_mode else {})}
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "")

    async def structure_text(self, text: str, schema_description: str, *, model: Optional[str]=None) -> Dict[str, Any]:
        system = ("You are a careful data-extraction assistant. "
                  "Return ONLY strict JSON, no markdown, no commentary.")
        user = (f"Extract data from the text and output JSON matching this schema.\n"
                f"SCHEMA: {schema_description}\n\nTEXT:\n{text}\n\n"
                "If a field is missing, use null or empty list. Output JSON only.")
        reply = await self._chat(
            [{"role":"system","content":system},{"role":"user","content":user}],
            json_mode=True, model=model
        )
        try:
            return json.loads(reply)
        except Exception:
            return json.loads(reply.strip().strip("`"))
