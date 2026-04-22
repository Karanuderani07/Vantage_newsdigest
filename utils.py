"""
utils.py — Shared helpers used across all nodes.
"""

import json
import time
import os
from datetime import datetime
from groq import Groq

# Initialise client once; nodes import this module.
_client: Groq | None = None


def get_client(api_key: str | None = None) -> Groq:
    global _client
    if _client is None:
        key = api_key or os.getenv("GROQ_API_KEY", "")
        _client = Groq(api_key=key)
    return _client


def llm(
    system: str,
    user: str,
    json_mode: bool = False,
    max_tokens: int = 1500,
    model: str = "llama-3.3-70b-versatile",
) -> str:
    """
    Call the Groq LLM. Retries once on transient failure.
    If json_mode=True, validates the response is parseable JSON.
    """
    client = get_client()
    for attempt in range(2):
        try:
            kwargs: dict = {}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                **kwargs,
            )
            text = resp.choices[0].message.content.strip()

            if json_mode:
                text = text.replace("```json", "").replace("```", "").strip()
                json.loads(text)  # validate — raises if invalid

            return text

        except Exception as e:
            if attempt == 0:
                log_print(f"⚠  Groq error ({e}), retrying in 2s…")
                time.sleep(2)
            else:
                raise


def stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_print(msg: str) -> None:
    print(f"  [{stamp()}] {msg}")