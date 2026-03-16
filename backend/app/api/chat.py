"""Chat API endpoint."""

from fastapi import APIRouter
from loguru import logger
from openai import AsyncOpenAI

from backend.app.core.config import settings
from backend.app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

SYSTEM_PROMPT = (
    "You are LifeOS, a proactive personal AI assistant. "
    "You help the user manage tasks, plans, and daily life. "
    "Be helpful, concise, and friendly. Reply in the same language as the user."
)


async def call_llm(message: str, system_prompt: str = "") -> str:
    """Call the configured LLM provider."""
    system_prompt = system_prompt or SYSTEM_PROMPT

    if settings.llm_provider == "anthropic":
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        resp = await client.messages.create(
            model=settings.llm_model or "claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )
        return resp.content[0].text

    # OpenAI-compatible providers (openai / deepseek)
    if settings.llm_provider == "deepseek":
        client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
        )
        model = settings.llm_model or "deepseek-chat"
    else:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        model = settings.llm_model or "gpt-4o-mini"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]
    resp = await client.chat.completions.create(
        model=model, messages=messages, max_tokens=1024
    )
    return resp.choices[0].message.content


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle a chat message. Week 1: direct LLM call, no agent orchestration yet."""
    logger.info(f"Chat request from user={request.user_id}: {request.message[:100]}")

    try:
        reply = await call_llm(request.message)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        reply = f"Sorry, I encountered an error: {e}"

    return ChatResponse(reply=reply, intent="chat")
