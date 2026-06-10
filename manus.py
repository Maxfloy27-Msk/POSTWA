import asyncio
import logging
import time
from typing import Callable, Optional

import aiohttp

from config import MANUS_API_KEY, MANUS_BASE_URL, POLL_INTERVAL, TASK_TIMEOUT

logger = logging.getLogger(__name__)

_HEADERS = {
    "Authorization": f"Bearer {MANUS_API_KEY}",
    "Content-Type": "application/json",
}


async def _post(endpoint: str, payload: dict) -> dict | list:
    url = f"{MANUS_BASE_URL}/{endpoint}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=_HEADERS, json=payload) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)


async def create_task(project_id: str, message: str) -> str:
    """Create a Manus task in the given project; return the task ID."""
    data = await _post("task.create", {"project_id": project_id, "message": message})
    if isinstance(data, dict):
        tid = data.get("id") or data.get("task_id") or data.get("taskId")
        if tid:
            return str(tid)
    raise ValueError(f"No task ID in Manus response: {data}")


async def list_messages(task_id: str) -> list[dict]:
    """Return all messages for a task."""
    data = await _post("task.listMessages", {"task_id": task_id})
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("messages", "data", "items", "result"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    return []


def _extract_text(messages: list[dict]) -> str:
    """Concatenate all assistant messages into one string."""
    parts = []
    for m in messages:
        if m.get("role") in ("assistant", "agent", "manus"):
            raw = m.get("content") or m.get("text") or m.get("message", "")
            if isinstance(raw, list):
                raw = "\n".join(
                    c.get("text", "") for c in raw if isinstance(c, dict) and c.get("text")
                )
            if raw:
                parts.append(str(raw).strip())
    return "\n\n".join(parts)


async def wait_for_result(
    task_id: str,
    on_tick: Optional[Callable[[int], None]] = None,
) -> str:
    """Poll task.listMessages until the response stabilises; return assistant text."""
    deadline = time.monotonic() + TASK_TIMEOUT
    await asyncio.sleep(20)  # give Manus time to start processing

    prev_count = -1
    stable_rounds = 0
    start = time.monotonic()

    while time.monotonic() < deadline:
        try:
            messages = await list_messages(task_id)
        except Exception as exc:
            logger.warning("Poll error (will retry): %s", exc)
            await asyncio.sleep(POLL_INTERVAL)
            continue

        has_assistant = any(m.get("role") in ("assistant", "agent", "manus") for m in messages)
        count = len(messages)

        if on_tick:
            await on_tick(int(time.monotonic() - start))

        if count == prev_count and has_assistant:
            stable_rounds += 1
            if stable_rounds >= 2:
                text = _extract_text(messages)
                if text:
                    return text
        else:
            stable_rounds = 0

        prev_count = count
        await asyncio.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Manus task {task_id} did not complete within {TASK_TIMEOUT}s")
