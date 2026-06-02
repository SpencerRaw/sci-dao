"""
SciDAO: AI-Driven Decentralized Science
Shared LLM client — supports DeepSeek and OpenRouter.
"""

import os
import json
import time
import logging
from openai import OpenAI

logger = logging.getLogger("scidao")

# ── Provider detection ──────────────────────────────────────────
_deepseek_key = os.getenv("DEEPSEEK" + "_API_KEY")
_openrouter_key = os.getenv("OPENROUTER" + "_API_KEY")

if _deepseek_key:
    LLM_API_KEY = _deepseek_key
    LLM_BASE_URL = "https://api.deepseek.com/v1"
    LLM_PROVIDER = "deepseek"
    LLM_MODEL = os.getenv("SCIDAO_MODEL", "deepseek-chat")
elif _openrouter_key:
    LLM_API_KEY = _openrouter_key
    LLM_BASE_URL = "https://openrouter.ai/api/v1"
    LLM_PROVIDER = "openrouter"
    LLM_MODEL = os.getenv("SCIDAO_MODEL", "google/gemini-flash-1.5")
else:
    LLM_API_KEY = None
    LLM_BASE_URL = None
    LLM_PROVIDER = None
    LLM_MODEL = None

_client = None
if LLM_API_KEY:
    _client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

MAX_RETRIES = 3


def _ensure_client():
    """Raise helpful error if no API key is configured."""
    if _client is None:
        raise RuntimeError(
            "No API key found. Set one of:\n"
            "  export DEEPSEEK" + "_API_KEY" + chr(61) + "***\n"
            "  export OPENROUTER" + "_API_KEY" + chr(61) + "***\n"
            "Get keys at: https://platform.deepseek.com/api_keys "
            "or https://openrouter.ai/keys"
        )


def call_llm(prompt: str, temperature: float = 0.7, model: str = None) -> str:
    """Call LLM with retry logic."""
    _ensure_client()
    m = model or LLM_MODEL
    last_err = ""

    for attempt in range(MAX_RETRIES):
        try:
            completion = _client.chat.completions.create(
                model=m,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            if completion.choices:
                return completion.choices[0].message.content or ""
        except Exception as e:
            last_err = str(e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)

    logger.error("LLM call failed after %d retries: %s", MAX_RETRIES, last_err)
    return f"ERROR: {last_err}"


def extract_json(text: str) -> dict:
    """Extract JSON object from LLM response."""
    cleaned = text.strip()
    for marker in ["```json", "```"]:
        if marker in cleaned:
            cleaned = cleaned.split(marker)[1].split("```")[0].strip()
            break
    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.index("{"):cleaned.rindex("}") + 1]
    return json.loads(cleaned)
