# 🤖 auto-lab

Fully automated daily AI engineering workspace.  
3 GitHub Actions commit real technical content every morning (Bangkok time) — zero manual action required after initial setup.

## What it does

| Workflow | Schedule (BKK) | Output | Source |
|----------|---------------|--------|--------|
| ArXiv Daily Digest | 08:00 every day | `papers/YYYY-MM-DD.md` | arxiv.org |
| HuggingFace Trending | 09:00 every day | `models/YYYY-MM-DD.md` | huggingface.co |
| Daily AI Snippet | 10:00 every day | `snippets/YYYY-MM-DD.py` | Gemini 1.5 Flash |
| Keepalive | Sunday 07:00 | — | internal |

## Cost

- GitHub Actions free tier: 2,000 min/month → this uses ~90 min/month
- ArXiv API: free, no key needed
- HuggingFace API: free, no key needed  
- Gemini 1.5 Flash: free tier (15 RPM, 1M tokens/day) → uses ~100 tokens/day

**Total cost: $0/month**

## Reliability

- All scripts have 3-attempt retry with exponential backoff
- All scripts write a fallback file if API is down (commit still happens)
- Keepalive workflow prevents 60-day inactivity disable
- `git pull --rebase` before every push prevents conflicts
