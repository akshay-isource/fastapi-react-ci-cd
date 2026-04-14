"""
LLM PROVIDER FACTORY

Single place to configure which LLM all agents use.
Change the provider in .env and the entire system switches.

WHY THIS MATTERS:
    - You're not locked into one vendor
    - Different agents can use different providers/models
    - Easy to switch if costs change or a provider goes down
    - You can test the same pipeline with different LLMs

SUPPORTED PROVIDERS:
    - anthropic  → Claude (claude-sonnet-4-20250514)
    - openai     → GPT (gpt-4o)
    - google     → Gemini (gemini-2.0-flash)
    - sarvam     → Sarvam AI (sarvam-m) — OpenAI-compatible API

TO ADD A NEW PROVIDER:
    1. pip install langchain-<provider>
    2. Add a new elif block below
    3. Add the API key to .env
    That's it.
"""

import os
from langchain_core.language_models.chat_models import BaseChatModel


# Default models per provider — override with LLM_MODEL in .env
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-20250514",
    "openai": "gpt-4o",
    "google": "gemini-2.0-flash",
    "sarvam": "sarvam-m",
}

# Providers that support tool/function calling
# If a provider is NOT in this set, agents will use fallback mode
TOOL_CALLING_PROVIDERS = {"anthropic", "openai", "google"}


def supports_tool_calling(provider: str | None = None) -> bool:
    """Check if the current LLM provider supports tool calling."""
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    return provider.lower().strip() in TOOL_CALLING_PROVIDERS


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> BaseChatModel:
    """
    Factory function that returns the right LLM based on provider.

    Args:
        provider: "anthropic", "openai", or "google".
                  Falls back to LLM_PROVIDER env var.
        model: Specific model name. Falls back to LLM_MODEL env var,
               then to DEFAULT_MODELS.
        temperature: Creativity level (0 = focused, 1 = creative)
        max_tokens: Hard cap on output tokens. Controls cost by
                    physically stopping generation after this many tokens.

    Returns:
        A LangChain chat model instance ready to use.

    Usage:
        llm = get_llm()                          # uses .env defaults
        llm = get_llm("openai", "gpt-4o-mini")   # explicit override
    """

    # Resolve provider: argument > env var > default
    provider = provider or os.getenv("LLM_PROVIDER", "anthropic")
    provider = provider.lower().strip()

    # Resolve model: argument > env var > default for provider
    model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider)

    # Build common kwargs — only include max_tokens if set
    # This avoids sending None which some providers reject
    extra = {}
    if max_tokens is not None:
        extra["max_tokens"] = max_tokens

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            **extra,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
            **extra,
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            **extra,
        )

    elif provider == "sarvam":
        # Sarvam AI exposes an OpenAI-compatible API, so we reuse ChatOpenAI
        # with a custom base_url pointing to Sarvam's endpoint.
        # No extra package needed — langchain-openai handles it.
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("SARVAM_API_KEY"),
            base_url="https://api.sarvam.ai/v1",
            **extra,
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Supported: anthropic, openai, google, sarvam"
        )
