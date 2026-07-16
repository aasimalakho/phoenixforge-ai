"""
Thin wrapper around whichever LLM provider is configured. Every agent calls
llm_client.ask(...) to do its reasoning. Supports Groq (default) or Anthropic.
"""
from .config import settings

_provider = settings.LLM_PROVIDER.lower()
_client = None

if _provider == "groq" and settings.GROQ_API_KEY:
    from groq import Groq
    _client = Groq(api_key=settings.GROQ_API_KEY)
elif _provider == "anthropic" and settings.ANTHROPIC_API_KEY:
    from anthropic import Anthropic
    _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def ask(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> str:
    if _client is None:
        key_name = "GROQ_API_KEY" if _provider == "groq" else "ANTHROPIC_API_KEY"
        return (
            f"[LLM DISABLED] No {key_name} was set in .env (LLM_PROVIDER={_provider}), so "
            f"PhoenixForge AI is running with reasoning disabled. Add your key to "
            f"backend/.env and restart the server to enable real agent reasoning.\n\n"
            f"(Would have asked: {user_prompt[:300]})"
        )

    if _provider == "groq":
        response = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()

    response = _client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(parts).strip()
