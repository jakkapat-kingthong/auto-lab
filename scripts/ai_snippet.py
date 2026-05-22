#!/usr/bin/env python3
"""
Generate a daily production-ready ML/AI Python snippet via Gemini 1.5 Flash.
- Topic rotates by day-of-year (deterministic, 30 topics = ~monthly cycle)
- Retry logic: 3 attempts with exponential backoff
- Fallback: writes a curated static snippet if Gemini API unavailable
- Always exits 0 (never fails the GitHub Actions workflow step)
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# ───────────────────────── constants ─────────────────────────

BANGKOK = timezone(timedelta(hours=7))
TODAY = datetime.now(BANGKOK).strftime("%Y-%m-%d")

API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta"
    "/models/gemini-1.5-flash:generateContent"
)

OUT_DIR = Path("snippets")
OUT_FILE = OUT_DIR / f"{TODAY}.py"

MAX_RETRIES = 3
BACKOFF_BASE = 5

# 30 topics หมุนเวียนตาม day-of-year — ครอบคลุม AI/ML stack ทั้งหมด
TOPICS: list[str] = [
    "async batch inference pipeline using httpx and asyncio.gather",
    "ONNX model export from PyTorch and optimized runtime inference",
    "FastAPI async endpoint with Pydantic v2 request and response models",
    "YOLOv8 custom inference loop with confidence filtering and NMS",
    "LangGraph single-node stateful agent with tool call support",
    "BM25 + dense hybrid retrieval with reciprocal rank fusion scoring",
    "Pydantic v2 settings management for ML pipeline configuration",
    "loguru structured JSON logging setup for FastAPI production",
    "pytest fixture pattern for ML model evaluation and benchmarking",
    "async retry decorator with exponential backoff for LLM API calls",
    "FAISS flat index build, save to disk, and k-NN search",
    "Docker healthcheck endpoint implementation with FastAPI",
    "streaming response from Gemini API using httpx async client",
    "RAG context builder with token budget enforcement and overflow handling",
    "LangSmith trace decorator for LLM function observability",
    "Gemini multimodal API call with base64 image and text input",
    "async producer-consumer queue for high-throughput CV inference",
    "Pydantic v2 discriminated union for multi-model output routing",
    "pytest-asyncio async test with FastAPI TestClient and mock LLM",
    "semantic chunking with sentence-transformers and cosine similarity",
    "Gemini function calling with structured JSON tool schema",
    "async rate limiter using asyncio.Semaphore and token bucket",
    "YOLOv8 to ONNX export with dynamic batch axes and validation",
    "FastAPI background task queue with polling status endpoint",
    "vector similarity search with numpy and cosine distance ranking",
    "OpenTelemetry trace span for FastAPI middleware observability",
    "ONNX Runtime session with IO binding for zero-copy inference",
    "LangGraph conditional edge routing with guard clause pattern",
    "async context manager for database connection pool management",
    "Pydantic v2 custom validator with field-level error aggregation",
]

# deterministic: วันที่ 1 = topic 0, วันที่ 2 = topic 1, ... วนซ้ำทุก 30 วัน
_doy = datetime.now(BANGKOK).timetuple().tm_yday
TOPIC = TOPICS[(_doy - 1) % len(TOPICS)]

PROMPT = f"""Write a production-ready Python 3.12 module for: {TOPIC}

Hard requirements (all must be present):
- `from __future__ import annotations` as first line
- Full type hints on every function, method, and variable
- loguru for all logging — absolutely no print() calls
- pydantic v2 for any data validation (BaseModel, Field, model_validator as needed)
- async/await wherever I/O or waiting is involved
- Specific exception types only — no bare `except`, no `except Exception` except at outermost
- Concise module-level docstring (1-2 sentences)
- 50–80 lines of substantive code (blank lines and comments don't count)
- Must be runnable as a standalone module or importable as a library

Output format:
- Raw Python code only
- No markdown code fences (no ```)
- No explanation text before or after
- No preamble like "Here is the code:"
"""

# Fallback snippet ใช้เมื่อ Gemini API ไม่พร้อม
FALLBACK_SNIPPET = '''"""
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
'''


# ───────────────────────── helpers ─────────────────────────

def build_payload() -> dict:
    return {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1500,
            "stopSequences": ["```"],  # ป้องกัน Gemini ใส่ markdown fence
        },
    }


def call_gemini_with_retry() -> str:
    """Call Gemini API with retry. Returns raw code string."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = httpx.post(
                f"{GEMINI_URL}?key={API_KEY}",
                json=build_payload(),
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            code = data["candidates"][0]["content"]["parts"][0]["text"]
            print(f"[snippet] Gemini success on attempt {attempt} ({len(code)} chars)")
            return code
        except httpx.HTTPStatusError as exc:
            print(f"[snippet] HTTP {exc.response.status_code} on attempt {attempt}")
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            print(f"[snippet] Network error on attempt {attempt}: {type(exc).__name__}")
        except (KeyError, IndexError) as exc:
            print(f"[snippet] Response parse error on attempt {attempt}: {exc}")

        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            print(f"[snippet] Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"[snippet] All {MAX_RETRIES} Gemini attempts failed")


def write_snippet(code: str, *, is_fallback: bool = False) -> None:
    """Write Python snippet to file with header."""
    OUT_DIR.mkdir(exist_ok=True)

    source_note = "Static fallback (Gemini API unavailable)" if is_fallback else "Gemini 1.5 Flash"
    header = (
        f'"""\n'
        f"Daily ML Snippet — {TODAY}\n"
        f"Topic: {TOPIC}\n"
        f"Source: {source_note}\n"
        f'"""\n'
    )

    # ลบ markdown fences ที่อาจติดมา
    clean = code.strip()
    for fence in ("```python", "```py", "```"):
        clean = clean.replace(fence, "")
    clean = clean.strip()

    OUT_FILE.write_text(header + "\n" + clean + "\n", encoding="utf-8")
    suffix = " [FALLBACK]" if is_fallback else ""
    print(f"[snippet] Wrote{suffix} → {OUT_FILE}")


# ───────────────────────── main ─────────────────────────

def main() -> None:
    if OUT_FILE.exists():
        print(f"[snippet] File already exists for {TODAY}, skipping.")
        return

    if not API_KEY:
        print("[snippet] GEMINI_API_KEY not set — writing fallback snippet.")
        write_snippet(FALLBACK_SNIPPET, is_fallback=True)
        return

    try:
        code = call_gemini_with_retry()
        write_snippet(code)
    except RuntimeError as exc:
        print(f"[snippet] {exc} — writing fallback snippet.")
        write_snippet(FALLBACK_SNIPPET, is_fallback=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[snippet] Unexpected error: {exc} — writing fallback snippet.")
        try:
            write_snippet(FALLBACK_SNIPPET, is_fallback=True)
        except Exception:
            pass  # ถ้าแม้แต่ write ก็ fail จบแล้ว
    sys.exit(0)
