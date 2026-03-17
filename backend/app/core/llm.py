"""Shared LLM call wrapper supporting multiple providers."""

from __future__ import annotations

import time

from loguru import logger

from backend.app.core.config import settings


async def call_llm(
    messages: list[dict[str, str]],
    caller: str = "",
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Call the configured LLM provider with a list of messages.

    Supports: openai, anthropic, deepseek, newapi.

    Provider/model resolution priority:
      1. Explicit ``provider``/``model`` arguments
      2. Per-caller overrides from ``LLM_CALLER_OVERRIDES`` in .env
      3. Global ``LLM_PROVIDER`` / ``LLM_MODEL`` defaults
    """
    # --- resolve effective provider & model ---
    override = settings.caller_overrides.get(caller, {}) if caller else {}
    effective_provider = provider or override.get("provider") or settings.llm_provider
    effective_model = model or override.get("model") or settings.llm_model

    tag = f"[LLM:{caller}]" if caller else "[LLM]"
    logger.debug(f"{tag} provider={effective_provider} model={effective_model}")
    logger.debug(f"{tag} Input messages ({len(messages)}):")
    for m in messages:
        role = m["role"]
        content = m["content"]
        preview = content[:200] + "..." if len(content) > 200 else content
        logger.debug(f"  {role}: {preview}")

    start = time.monotonic()

    if effective_provider == "anthropic":
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        system_msg = ""
        chat_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_msgs.append(m)
        resp = await client.messages.create(
            model=effective_model or "claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_msg,
            messages=chat_msgs,
        )
        text = resp.content[0].text
    else:
        # OpenAI-compatible: openai / deepseek / newapi
        from openai import AsyncOpenAI

        if effective_provider == "newapi":
            client = AsyncOpenAI(
                api_key=settings.newapi_api_key,
                base_url=settings.newapi_base_url,
            )
        elif effective_provider == "deepseek":
            client = AsyncOpenAI(
                api_key=settings.deepseek_api_key,
                base_url="https://api.deepseek.com/v1",
            )
        else:
            # default: openai
            client = AsyncOpenAI(api_key=settings.openai_api_key)

        used_model = effective_model or "gpt-4o-mini"
        resp = await client.chat.completions.create(
            model=used_model, messages=messages, max_tokens=1024
        )
        text = resp.choices[0].message.content

    elapsed = time.monotonic() - start
    logger.info(
        f"{tag} [{effective_provider}/{effective_model}] "
        f"Done in {elapsed:.1f}s, output {len(text)} chars"
    )
    logger.debug(f"{tag} Output: {text[:300]}{'...' if len(text) > 300 else ''}")
    return text
