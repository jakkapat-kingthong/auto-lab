#!/usr/bin/env python3
"""
Fetch HuggingFace top trending models and write daily markdown snapshot.
- Retry logic: 3 attempts with exponential backoff
- Fallback: always creates a file even if API fails (ensures commit happens)
- Always exits 0 (never fails the GitHub Actions workflow step)
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# ───────────────────────── constants ─────────────────────────

BANGKOK = timezone(timedelta(hours=7))
TODAY = datetime.now(BANGKOK).strftime("%Y-%m-%d")

HF_API = "https://huggingface.co/api/models?sort=trending&direction=-1&limit=10"

OUT_DIR = Path("models")
OUT_FILE = OUT_DIR / f"{TODAY}.md"

MAX_RETRIES = 3
BACKOFF_BASE = 5


# ───────────────────────── helpers ─────────────────────────

def fetch_with_retry(url: str) -> list[dict]:
    """Fetch HuggingFace API with retry. Returns parsed JSON list."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                url,
                headers={"Accept": "application/json"},
                timeout=30,
                follow_redirects=True,
            )
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list):
                raise ValueError(f"Unexpected response type: {type(data)}")
            print(f"[hf] Fetch success on attempt {attempt}: {len(data)} models")
            return data
        except httpx.HTTPStatusError as exc:
            print(f"[hf] HTTP {exc.response.status_code} on attempt {attempt}")
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            print(f"[hf] Network error on attempt {attempt}: {type(exc).__name__}")
        except ValueError as exc:
            print(f"[hf] Parse error on attempt {attempt}: {exc}")

        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            print(f"[hf] Retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"[hf] All {MAX_RETRIES} attempts failed")


def write_snapshot(models: list[dict]) -> None:
    """Write trending models to markdown table."""
    OUT_DIR.mkdir(exist_ok=True)

    lines: list[str] = [
        f"# 🤗 HuggingFace Trending — {TODAY}\n",
        "\n",
        "> Auto-fetched daily | Top 10 trending models\n",
        "\n",
        "| # | Model | Downloads | Likes | Task |\n",
        "|---|-------|----------:|------:|------|\n",
    ]

    for i, m in enumerate(models[:10], 1):
        model_id: str = m.get("id", "unknown")
        downloads: int = m.get("downloads", 0)
        likes: int = m.get("likes", 0)
        task: str = m.get("pipeline_tag") or "—"
        url = f"https://huggingface.co/{model_id}"
        lines.append(
            f"| {i} | [{model_id}]({url}) | {downloads:,} | {likes:,} | {task} |\n"
        )

    lines.append(f"\n*Updated: {datetime.now(BANGKOK).strftime('%Y-%m-%d %H:%M')} BKK*\n")

    OUT_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"[hf] Wrote {min(len(models), 10)} models → {OUT_FILE}")


def write_fallback(reason: str) -> None:
    """Write fallback file when API fails — ensures commit still happens."""
    OUT_DIR.mkdir(exist_ok=True)
    content = (
        f"# 🤗 HuggingFace Trending — {TODAY}\n\n"
        f"> ⚠️ Auto-fetch unavailable: {reason}\n\n"
        f"Check [huggingface.co/models](https://huggingface.co/models?sort=trending) directly.\n"
    )
    OUT_FILE.write_text(content, encoding="utf-8")
    print(f"[hf] Wrote fallback file → {OUT_FILE}")


# ───────────────────────── main ─────────────────────────

def main() -> None:
    if OUT_FILE.exists():
        print(f"[hf] File already exists for {TODAY}, skipping.")
        return

    try:
        models = fetch_with_retry(HF_API)

        if not models:
            write_fallback("Empty response from API")
            return

        write_snapshot(models)

    except RuntimeError as exc:
        print(f"[hf] {exc}")
        write_fallback(str(exc))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[hf] Unexpected error: {exc}")
        write_fallback(f"Unexpected error: {exc}")
    sys.exit(0)
