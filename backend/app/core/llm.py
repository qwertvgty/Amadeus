"""Shared LLM call wrapper supporting multiple providers."""

from __future__ import annotations

from backend.app.core.config import settings


async def call_llm(messages: list[dict[str, str]]) -> str:
    """Call the configured LLM provider with a list of messages.

    Supports: openai, anthropic, deepseek.
    """
    if settings.llm_provider == "anthropic":
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
            model=settings.llm_model or "claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_msg,
            messages=chat_msgs,
        )
        return resp.content[0].text

    # OpenAI-compatible (openai / deepseek)
    from openai import AsyncOpenAI

    if settings.llm_provider == "deepseek":
        client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
        )
        model = settings.llm_model or "deepseek-chat"
    else:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        model = settings.llm_model or "gpt-4o-mini"

    resp = await client.chat.completions.create(
        model=model, messages=messages, max_tokens=1024
    )
    return resp.choices[0].message.content
