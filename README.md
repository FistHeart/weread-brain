# WRS001 — WeReadSync

> Sync WeChat Reading notes & highlights to local Markdown files. Build your personal knowledge base, Obsidian-ready.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)

## What It Does

- Connects to [WeChat Reading Skills API](https://weread.qq.com/r/weread-skills) (official, released 2026-05-17)
- Syncs all your **highlights** (划线) and **personal notes** (想法) to local Markdown files
- Organized by book title — each book gets its own `.md` file
- Ready to open as an **Obsidian vault** — with YAML frontmatter, `[[wikilinks]]` compatible
- Hourly incremental sync via cron — only updates changed books

## Quick Start

### 1. Install the Skill

```bash
npx skills add Tencent/WeChatReading -g
```

### 2. Get Your API Key

Visit [https://weread.qq.com/r/weread-skills](https://weread.qq.com/r/weread-skills), scan the QR code with WeChat, and copy your API Key (starts with `wrk-`).

### 3. Clone & Configure

```bash
git clone https://github.com/YOUR_USERNAME/WRS001.git
cd WRS001
cp config/.env.example config/.env
# Edit config/.env and paste your API key
```

### 4. Sync

```bash
python src/weread_sync.py
```

Output lands in `output/` — open it directly as an Obsidian vault:

```bash
open output/   # macOS
# or add it as an Obsidian vault via Obsidian GUI
```

## AI Agent Command

To let any AI agent (Claude Code, ChatGPT, Cursor, etc.) sync your WeRead notes:

```bash
cd /path/to/WRS001 && python src/weread_sync.py
```

**One-liner for cron / agent automation:**

```bash
WEREAD_API_KEY=wrk-xxx python src/weread_sync.py --incremental --output ./output/
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `python src/weread_sync.py` | Full sync — all books |
| `python src/weread_sync.py --incremental` | Incremental sync — only changed books |
| `python src/weread_sync.py --output ~/ObsidianVault/` | Custom output directory |
| `python src/weread_sync.py --setup` | Interactive setup wizard |
| `python src/weread_sync.py --cleanup` | Remove books deleted from WeRead |

## Automated Hourly Sync

```bash
# Add to crontab (runs at minute 7 every hour)
crontab -e
7 * * * * cd /path/to/WRS001 && python src/weread_sync.py --incremental >> sync.log 2>&1
```

## Output Format

Each synced book generates a `.md` file:

```markdown
---
title: "Sapiens"
author: "Yuval Noah Harari"
tags: [weread, book-notes]
lastSync: "2026-06-26"
---

# Sapiens

**Author**: Yuval Noah Harari

---

## Highlights & Notes

> Culture tends to argue that it forbids only that which is unnatural.
  — Chapter 6
  2026-06-25 14:30

> **Note:** This explains why taboos vary so much across cultures.
  2026-06-25 14:31

---

## My Thoughts

> Biology enables, culture forbids.
  — Chapter 6
**Thought:** The tension between biology and culture is the engine of history.
  2026-06-26 08:15
```

## Project Structure

```
WRS001/
├── README.md
├── .gitignore
├── LICENSE
├── config/
│   └── .env.example       # API key template (real key in .env, gitignored)
├── src/
│   └── weread_sync.py     # Core sync engine
├── output/                # Synced Markdown files (gitignored)
└── setup.sh               # One-click setup script
```

## Security

- API Key is **never hardcoded** — loaded from environment variable or `config/.env`
- `config/.env` and `output/` are in `.gitignore` — never committed to git
- API Key is **never logged** or written to output files
- All API calls use HTTPS (TLS 1.2+)

## Requirements

- Python 3.9+
- `requests` library (`pip install requests`)
- WeChat Reading account with API Key

## License

MIT — see [LICENSE](LICENSE) file.

## Related

- [WeChat Reading Skills](https://weread.qq.com/r/weread-skills) — Official API documentation
- [Karpathy LLM Wiki](https://github.com/Astro-Han/karpathy-llm-wiki-bootstrap) — Inspiration for personal knowledge base methodology
- [Obsidian](https://obsidian.md) — Recommended Markdown knowledge base app
