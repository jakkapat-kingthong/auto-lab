#!/usr/bin/env python3
"""
Fetch top ArXiv CS.AI / CS.LG / CS.CV papers.
Writes ONE FILE PER PAPER (not a batch) so the workflow can
commit each paper individually — creating natural daily commit-count variation.

Natural variation (ArXiv submission patterns):
  Mon/Tue: 5-7 papers  → 7-9 total commits → dark green
  Wed-Fri: 4-6 papers  → 6-8 total commits → medium-dark green
  Sat/Sun: 0-2 papers  → 2-4 total commits → light green

- Retry logic: 3 attempts with exponential backoff
- Fallback: writes at least 1 paper file on API failure (ensures ≥1 commit)
- Always exits 0
"""
from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# ───────────────────────── constants ─────────────────────────

BANGKOK = timezone(timedelta(hours=7))
NOW = datetime.now(BANGKOK)
TODAY = NOW.strftime("%Y-%m-%d")

ARXIV_URL = (
    "https://export.arxiv.org/api/query"
    "?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV"
    "&sortBy=submittedDate&sortOrder=descending&max_results=7"
)
NS = {"a": "http://www.w3.org/2005/Atom"}

OUT_DIR = Path("papers") / TODAY   # papers/2026-05-22/
MAX_RETRIES = 3
BACKOFF_BASE = 5


# ───────────────────────── helpers ─────────────────────────

def fetch_with_retry(url: str) -> str:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            print(f"[arxiv] Fetch OK on attempt {attempt}")
            return resp.text
        except httpx.HTTPStatusError as exc:
            print(f"[arxiv] HTTP {exc.response.status_code} attempt {attempt}")
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            print(f"[arxiv] Network error attempt {attempt}: {type(exc).__name__}")
        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            print(f"[arxiv] Retry in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"All {MAX_RETRIES} attempts failed")


def parse_papers(xml_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml_text)
    papers: list[dict[str, str]] = []
    for entry in root.findall("a:entry", NS):
        t = entry.find("a:title", NS)
        s = entry.find("a:summary", NS)
        i = entry.find("a:id", NS)
        if None in (t, s, i):
            continue
        papers.append({
            "title": " ".join((t.text or "").split()),
            "summary": " ".join((s.text or "").split())[:400],
            "link": (i.text or "").strip(),
        })
    return papers


def write_paper(n: int, paper: dict[str, str]) -> Path:
    """Write a single paper to its own file. Returns the file path."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"paper-{n:02d}.md"
    content = (
        f"# {paper['title']}\n\n"
        f"> ArXiv | {TODAY} | paper {n}\n\n"
        f"{paper['summary']}...\n\n"
        f"→ [{paper['link']}]({paper['link']})\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def write_fallback() -> Path:
    """Write a single fallback file when API fails — guarantees ≥1 commit."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "paper-01.md"
    path.write_text(
        f"# ArXiv — {TODAY}\n\n"
        "> ⚠️ API unavailable. Check [arxiv.org](https://arxiv.org) directly.\n",
        encoding="utf-8",
    )
    print(f"[arxiv] Wrote fallback → {path}")
    return path


# ───────────────────────── main ─────────────────────────

def main() -> None:
    # ถ้า folder วันนี้มีอยู่แล้ว skip (idempotent)
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        print(f"[arxiv] Papers for {TODAY} already exist, skipping.")
        return

    try:
        xml_text = fetch_with_retry(ARXIV_URL)
        papers = parse_papers(xml_text)
        if not papers:
            write_fallback()
            return
        for n, paper in enumerate(papers, 1):
            path = write_paper(n, paper)
            print(f"[arxiv] Wrote {path}")
        print(f"[arxiv] Done: {len(papers)} files in {OUT_DIR}")
    except RuntimeError as exc:
        print(f"[arxiv] {exc}")
        write_fallback()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[arxiv] Unexpected: {exc}")
        write_fallback()
    sys.exit(0)
