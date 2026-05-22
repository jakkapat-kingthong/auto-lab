#!/usr/bin/env python3
"""
Daily activity pulse generator — smooth noise algorithm.

สร้าง N commit ต่อวันโดยใช้ smooth hash noise:
- Week-level energy: ทั้งสัปดาห์มี "tone" คล้ายกัน (sprint effect)
- Weekday multiplier: วันธรรมดา > วันหยุด
- Daily jitter: ±15% random noise ต่อวัน
- Spike event: 12% ของวันธรรมดา = commit สูงผิดปกติ
- Rest event: 8% ของวันธรรมดา = commit ต่ำผิดปกติ

Output: N ไฟล์ journal entries ที่ workflow จะ commit ทีละไฟล์
"""
from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BANGKOK = timezone(timedelta(hours=7))
NOW = datetime.now(BANGKOK)
TODAY = NOW.strftime("%Y-%m-%d")
OUT_DIR = Path("journal") / TODAY

# Session activities หมุนเวียน — ดูเหมือน work log จริง
ACTIVITIES: list[str] = [
    "Review PR and leave inline comments",
    "Refactor data pipeline for clarity",
    "Add unit tests for edge cases",
    "Update documentation and examples",
    "Debug inference latency issue",
    "Optimize model loading sequence",
    "Write integration test for API endpoint",
    "Clean up deprecated helper functions",
    "Benchmark retrieval pipeline performance",
    "Fix type hints and linting warnings",
    "Add logging to async queue handler",
    "Profile memory usage during batch inference",
    "Restructure config management module",
    "Update dependency versions in pyproject.toml",
    "Investigate CI failure on Python 3.12",
    "Improve error messages for validation failures",
    "Add retry logic to external API client",
    "Document architecture decision for RAG pipeline",
    "Implement graceful shutdown for FastAPI app",
    "Tune chunking parameters for retrieval quality",
    "Write smoke test for Docker deployment",
    "Review and merge upstream changes",
    "Add monitoring metrics to inference endpoint",
    "Refactor prompt templates for consistency",
    "Validate ONNX export matches PyTorch output",
]


def _hash_float(key: str) -> float:
    """Deterministic float [0, 1) from any string key."""
    digest = hashlib.sha256(key.encode()).hexdigest()[:8]
    return int(digest, 16) / 0xFFFFFFFF


def daily_pulse_count(d_str: str) -> int:
    """
    Smooth noise commit count for a given date string (YYYY-MM-DD).

    Algorithm produces values in range 0–11 with:
    - Natural weekly rhythm (Mon-Fri active, Sat-Sun quiet)
    - Week-level clustering (consecutive days share similar energy)
    - Occasional spikes and rest days
    """
    from datetime import date
    d = date.fromisoformat(d_str)
    iso = d.isocalendar()
    week_key = f"{iso[0]}-W{iso[1]:02d}"

    # 1. Week energy — same key for all days in a week → sprint clustering
    week_energy = _hash_float(week_key)

    # 2. Weekday multiplier
    weekday = d.weekday()  # 0=Mon, 6=Sun
    multipliers = [1.0, 1.1, 0.95, 1.0, 0.80, 0.20, 0.10]
    day_mult = multipliers[weekday]

    # 3. Per-day jitter ±15%
    jitter = (_hash_float(f"jitter-{d_str}") - 0.5) * 0.30

    # 4. Events (only on weekdays)
    is_weekday = weekday < 5
    is_spike = _hash_float(f"spike-{d_str}") < 0.12 and is_weekday
    is_rest  = _hash_float(f"rest-{d_str}")  < 0.08 and is_weekday

    energy = max(0.0, min(1.0, week_energy * day_mult + jitter))

    if is_rest:
        return max(0, int(energy * 2))       # 0–1
    if is_spike:
        return int(energy * 5) + 6          # 6–11
    return int(energy * 6)                  # 0–5


def pick_activity(session: int, d_str: str) -> str:
    idx = int(_hash_float(f"act-{d_str}-{session}") * len(ACTIVITIES))
    return ACTIVITIES[idx % len(ACTIVITIES)]


def write_sessions(count: int) -> list[Path]:
    """Write `count` individual session files. Returns list of written paths."""
    if count == 0:
        print(f"[pulse] Rest day for {TODAY} — 0 sessions")
        return []

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for i in range(1, count + 1):
        activity = pick_activity(i, TODAY)
        session_time = NOW.replace(
            hour=9 + (i - 1) * 1,  # 09:00, 10:00, 11:00 ...
            minute=int(_hash_float(f"min-{TODAY}-{i}") * 59),
            second=0,
        )
        time_str = session_time.strftime("%H:%M")

        content = (
            f"# Lab Journal — {TODAY} — Session {i}/{count}\n\n"
            f"**Time:** {time_str} BKK  \n"
            f"**Activity:** {activity}\n\n"
            f"---\n"
            f"*Auto-logged by auto-lab pulse*\n"
        )
        path = OUT_DIR / f"session-{i:02d}.md"
        path.write_text(content, encoding="utf-8")
        paths.append(path)

    print(f"[pulse] Wrote {count} sessions → {OUT_DIR}")
    return paths


def main() -> None:
    # Idempotent: skip if already ran today
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        print(f"[pulse] Sessions for {TODAY} already exist, skipping.")
        return

    count = daily_pulse_count(TODAY)
    write_sessions(count)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[pulse] Error: {exc}")
    sys.exit(0)
