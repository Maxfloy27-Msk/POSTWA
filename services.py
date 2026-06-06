import asyncio
import logging
from typing import Any

import aiohttp

from config import AUTO_POST_WA_URL, REQUEST_TIMEOUT, SMM_WINNI2_URL

logger = logging.getLogger(__name__)


async def generate_posts(user_id: int, text: str) -> list[str]:
    """Send user text to SMM WINNI2 webhook and return generated posts."""
    if not SMM_WINNI2_URL:
        raise RuntimeError("SMM_WINNI2_URL is not configured")

    payload = {"user_id": user_id, "text": text}
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(SMM_WINNI2_URL, json=payload) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)

    return _extract_posts(data)


async def send_to_auto_post_wa(user_id: int, posts: list[str]) -> None:
    """Forward generated posts to the Auto_post_WA webhook."""
    if not AUTO_POST_WA_URL:
        logger.warning("AUTO_POST_WA_URL is not configured, skipping WA delivery")
        return

    payload = {"user_id": user_id, "posts": posts}
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(AUTO_POST_WA_URL, json=payload) as resp:
            resp.raise_for_status()


def _extract_posts(data: Any) -> list[str]:
    """SMM WINNI2 may return posts in several shapes — normalise to list[str]."""
    if isinstance(data, list):
        return [str(item) for item in data if item]
    if isinstance(data, dict):
        for key in ("posts", "result", "data", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return [str(item) for item in value if item]
            if isinstance(value, str) and value:
                return [value]
        if "text" in data and isinstance(data["text"], str):
            return [data["text"]]
    if isinstance(data, str) and data:
        return [data]
    return []


async def deliver_posts(send_to_user, user_id: int, posts: list[str]) -> None:
    """Deliver posts to user chat and Auto_post_WA in parallel."""
    await asyncio.gather(
        _send_all_to_user(send_to_user, posts),
        send_to_auto_post_wa(user_id, posts),
        return_exceptions=False,
    )


async def _send_all_to_user(send_to_user, posts: list[str]) -> None:
    for post in posts:
        await send_to_user(post)
