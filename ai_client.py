import os
from enum import Enum

import aiohttp

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SMM_PROMPT = (
    "Ты профессиональный SMM-специалист. "
    "Напиши 3 поста для социальных сетей на основе темы пользователя. "
    "Посты должны быть живыми, вовлекающими, с хэштегами. "
    "Разделяй посты символом ---."
)


class AIProvider(str, Enum):
    CLAUDE = "claude"
    CHATGPT = "chatgpt"


async def generate_with_claude(user_text: str) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY не задан в .env")

    payload = {
        "model": "claude-opus-4-8",
        "max_tokens": 2048,
        "system": SMM_PROMPT,
        "messages": [{"role": "user", "content": user_text}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"Claude API error {resp.status}: {data}")
            return data["content"][0]["text"]


async def generate_with_chatgpt(user_text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY не задан в .env")

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": SMM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 2048,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "content-type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"ChatGPT API error {resp.status}: {data}")
            return data["choices"][0]["message"]["content"]


async def generate_posts(user_text: str, provider: AIProvider) -> str:
    if provider == AIProvider.CLAUDE:
        return await generate_with_claude(user_text)
    return await generate_with_chatgpt(user_text)
