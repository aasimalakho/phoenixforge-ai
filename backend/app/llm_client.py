"""
Thin wrapper around the Anthropic API. Every agent calls llm_client.ask(...) to do its
reasoning (root cause analysis, blast-radius explanations, generated SQL/DAG code, PR
descriptions, natural-language chat answers, etc).

Keeping this in one place means you only need to change one file if you ever want to
swap models or add retries/caching.
"""
from anthropic import Anthropic
from .config import settings

_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None


def ask(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    """Send a system+user prompt to Claude and return the plain text response."""
    if _client is None:
        return (
            "[LLM DISABLED] No ANTHROPIC_API_KEY was set in .env, so PhoenixForge AI is "
            "running with reasoning disabled. Add your key to backend/.env and restart "
            "the server to enable real agent reasoning.\n\n"
            f"(Would have asked: {user_prompt[:300]})"
        )

    response = _client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts).strip()
