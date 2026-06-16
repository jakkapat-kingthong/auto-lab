"""
Daily ML Snippet — 2026-06-16
Topic: async producer-consumer queue for high-throughput CV inference
Source: Static fallback (Gemini API unavailable)
"""

"""
Async retry decorator with exponential backoff for LLM API calls.
Static fallback — generated when Gemini API was unavailable.
"""
from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable, Awaitable
from typing import TypeVar, ParamSpec

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def async_retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator: retry an async function with exponential backoff.

    Args:
        max_attempts: Maximum number of total attempts (including first).
        backoff_base: Base wait time in seconds (doubles each retry).
        exceptions: Exception types that trigger a retry.
    """
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            "Succeeded after retry",
                            func=func.__name__,
                            attempt=attempt,
                        )
                    return result
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(
                            "All attempts exhausted",
                            func=func.__name__,
                            attempts=max_attempts,
                            error=str(exc),
                        )
                        break
                    wait = backoff_base * (2 ** (attempt - 1))
                    logger.warning(
                        "Attempt failed, retrying",
                        func=func.__name__,
                        attempt=attempt,
                        wait_seconds=wait,
                        error=str(exc),
                    )
                    await asyncio.sleep(wait)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ── Example usage ────────────────────────────────────────────────
import httpx

@async_retry(max_attempts=3, backoff_base=2.0, exceptions=(httpx.HTTPError,))
async def call_llm_api(prompt: str) -> str:
    """Call an LLM API endpoint with automatic retry on HTTP errors."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.example.com/generate",
            json={"prompt": prompt},
        )
        resp.raise_for_status()
        return resp.json()["text"]
