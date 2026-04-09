from __future__ import annotations

import json
from typing import Any, Optional
from urllib.request import Request, urlopen

from app.core.config import settings


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```json"):
        return s.replace("```json", "").replace("```", "").strip()
    if s.startswith("```"):
        return s.replace("```", "").strip()
    return s


class LLMClient:
    def chat_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.0,
        response_format: Optional[dict[str, Any]] = None,
    ) -> str:
        if not settings.api_key:
            raise RuntimeError("Missing API key (OPENAI_API_KEY or OPENROUTER_API_KEY).")

        body: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        if response_format is not None:
            body["response_format"] = response_format

        req = Request(
            f"{settings.endpoint}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        if settings.openrouter_site_url:
            req.add_header("HTTP-Referer", settings.openrouter_site_url)
        if settings.openrouter_site_name:
            req.add_header("X-Title", settings.openrouter_site_name)

        with urlopen(req, timeout=settings.timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return str(payload["choices"][0]["message"]["content"] or "")

    def chat_completion_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        content = self.chat_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        cleaned = _strip_code_fence(content)
        return json.loads(cleaned, strict=False)


llm_client = LLMClient()

