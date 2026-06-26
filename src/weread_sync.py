#!/usr/bin/env python3
"""
WeReadSync — 微信读书笔记 → 本地 Markdown 知识库

Usage:
    python src/weread_sync.py                     # Full sync
    python src/weread_sync.py --incremental       # Incremental (only changed books)
    python src/weread_sync.py --output ~/notes/   # Custom output directory
    python src/weread_sync.py --setup             # Interactive setup guide

API Key: Get from https://weread.qq.com/r/weread-skills
         Store as WEREAD_API_KEY env var or in config/.env

Security: API key never logged, never stored in output files.
"""

import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

# ── Constants ──────────────────────────────────────────
GATEWAY_URL = "https://i.weread.qq.com/api/agent/gateway"
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_api_key() -> str:
    """Load API key from env var or config file (never hardcoded)."""
    sources = [
        os.environ.get("WEREAD_API_KEY"),
        os.environ.get("WEREAD_TOKEN"),
    ]
    # Check config/.env
    env_file = PROJECT_ROOT / "config" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("WEREAD_API_KEY="):
                sources.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
            elif line.startswith("WEREAD_TOKEN="):
                sources.append(line.split("=", 1)[1].strip().strip('"').strip("'"))

    for key in sources:
        if key and key.startswith("wrk-"):
            return key

    print("=" * 60)
    print("  WeRead API Key 未找到")
    print("=" * 60)
    print()
    print("  获取方式:")
    print("  1. 访问 https://weread.qq.com/r/weread-skills")
    print("  2. 微信扫码登录, 复制 API Key (wrk-... 开头)")
    print()
    print("  配置方式 (任选一种):")
    print("  A) export WEREAD_API_KEY='wrk-...'")
    print("  B) echo 'wrk-...' > config/.env")
    print()
    print("  或运行: python src/weread_sync.py --setup")
    sys.exit(1)


class WeReadSync:
    """微信读书笔记同步引擎.

    Uses the official WeRead Agent Gateway API (released 2026-05-17).
    Endpoints: /shelf/sync, /book/bookmarklist, /review/list/mine, /book/info
    """

    def __init__(self, api_key: str, output_dir: str = ""):
        self._key = api_key
        self._output = Path(output_dir or DEFAULT_OUTPUT)
        self._output.mkdir(parents=True, exist_ok=True)
        self._sess = self._build_session()

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "User-Agent": "WeReadSync/1.0 (CLI; +https://github.com)",
        })
        return s

    # ── API ────────────────────────────────────────────

    def _call(self, api_name: str, params=None) -> dict:
        """Call the WeRead Agent Gateway API."""
        body = {"api_name": api_name}
        if params:
            body.update(params)
        for attempt in range(3):
            try:
                r = self._sess.post(GATEWAY_URL, json=body, timeout=20)
                if r.status_code == 200:
                    return r.json()
                if r.status_code == 429:
                    time.sleep(2 * (attempt + 1))
                    continue
                return {}
            except requests.RequestException:
                if attempt < 2:
                    time.sleep(2)
        return {}

    def get_notebooks(self) -> list[dict]:
        data = self._call("/user/notebooks")
        return data.get("books", [])

    def get_bookmarks(self, book_id: str) -> list[dict]:
        data = self._call("/book/bookmarklist", {"bookId": book_id})
        return data.get("updated", [])

    def get_reviews(self, book_id: str) -> list[dict]:
        data = self._call("/review/list/mine", {"bookid": book_id})
        return data.get("reviews", [])

    def get_book_info(self, book_id: str) -> dict:
        data = self._call("/book/info", {"bookId": book_id})
        return data.get("book", {})

    # ── Format ─────────────────────────────────────────

    @staticmethod
    def _to_markdown(book: dict, bookmarks: list, reviews: list) -> str:
        title = book.get("title", "Unknown")
        author = book.get("author", "")
        translator = book.get("translator", "")
        intro = book.get("intro") or book.get("description") or ""
        book_id = book.get("bookId", "")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        lines = [
            "---",
            f'title: "{title}"',
            f'author: "{author}"',
            f"tags: [weread, book-notes]",
            f'lastSync: "{now}"',
            "---",
            "",
            f"# {title}",
            "",
            f"**Author**: {author}",
        ]
        if translator:
            lines.append(f"**Translator**: {translator}")
        lines.append("")

        if intro and len(intro) > 10:
            lines.append(f"> {intro[:300]}{'...' if len(intro) > 300 else ''}")
            lines.append("")

        # Highlights + inline thoughts
        if bookmarks:
            lines += ["---", "", "## Highlights & Notes", ""]
            for bm in bookmarks:
                mark = bm.get("markText", "")
                note = bm.get("content", "")
                chapter = bm.get("chapterName", "")
                ct = bm.get("createTime", 0)
                ts = datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M") if ct else ""
                if mark:
                    lines.append(f"> {mark}")
                    if chapter:
                        lines.append(f"  — {chapter}")
                    if ts:
                        lines.append(f"  {ts}")
                    lines.append("")
                if note and note != mark:
                    lines.append(f"> **Note:** {note}")
                    if ts:
                        lines.append(f"  {ts}")
                    lines.append("")

        # Standalone thoughts (deduplicated)
        existing = {bm.get("content", "").strip() for bm in bookmarks if bm.get("content")}
        unique_reviews = [
            (rv.get("review", rv)) for rv in reviews
            if (rv.get("review", rv)).get("content", "").strip() not in existing
        ]
        if unique_reviews:
            lines += ["---", "", "## My Thoughts", ""]
            for inner in unique_reviews:
                ct = inner.get("createTime", 0)
                ts = datetime.fromtimestamp(ct).strftime("%Y-%m-%d %H:%M") if ct else ""
                content = inner.get("content", "")
                abstract = inner.get("abstract", "")
                chapter = inner.get("chapterTitle") or inner.get("chapterName", "")
                if abstract:
                    lines.append(f"> {abstract[:300]}")
                    if chapter:
                        lines.append(f"  — {chapter}")
                if content:
                    lines.append(f"**Thought:** {content}")
                if ts:
                    lines.append(f"  {ts}")
                lines.append("")

        if book_id:
            lines += ["---", "", f"[Open in WeRead](weread://reading?bId={book_id})", ""]

        return "\n".join(lines)

    # ── Sync ──────────────────────────────────────────

    def sync_book(self, entry: dict, incremental: bool = False) -> int:
        """Sync one book. Returns 1 if updated, 0 if skipped."""
        b = entry.get("book", entry)
        book_id = b.get("bookId", "")
        title = b.get("title", "Unknown")
        if not book_id:
            return 0

        bookmarks = self.get_bookmarks(book_id)
        reviews = self.get_reviews(book_id)
        total = len(bookmarks) + len(reviews)

        md = self._to_markdown(b, bookmarks, reviews)
        safe_name = title.replace("/", "_").replace(":", "：") + ".md"
        fpath = self._output / safe_name

        if incremental and fpath.exists():
            old = hashlib.md5(fpath.read_bytes()).hexdigest()
            new = hashlib.md5(md.encode()).hexdigest()
            if old == new:
                return 0

        fpath.write_text(md, encoding="utf-8")
        return 1

    def sync_all(self, incremental: bool = False) -> dict:
        """Sync all books with notes. Returns {synced, skipped, total}."""
        books = self.get_notebooks()
        if not books:
            return {"error": "no_books", "synced": 0, "skipped": 0, "total": 0}

        synced = 0
        for entry in books:
            try:
                synced += self.sync_book(entry, incremental)
            except Exception:
                pass
            time.sleep(0.3)

        return {
            "synced": synced,
            "skipped": len(books) - synced,
            "total": len(books),
        }

    # ── Cleanup ────────────────────────────────────────

    def cleanup_stale(self) -> int:
        """Remove .md files for books no longer in the notebook list."""
        books = self.get_notebooks()
        valid_titles = set()
        for entry in books:
            b = entry.get("book", entry)
            title = b.get("title", "")
            if title:
                valid_titles.add(title.replace("/", "_").replace(":", "："))

        removed = 0
        for f in self._output.glob("*.md"):
            if f.stem not in valid_titles:
                f.unlink()
                removed += 1
        return removed


# ── CLI ───────────────────────────────────────────────

def cmd_setup():
    """Interactive setup guide."""
    print("=" * 60)
    print("  WeReadSync — 微信读书笔记同步工具 安装指南")
    print("=" * 60)
    print()
    print("Step 1: 获取 API Key")
    print("  访问 https://weread.qq.com/r/weread-skills")
    print("  微信扫码登录，复制显示的 API Key (wrk-... 开头)")
    print()
    print("Step 2: 配置 API Key")
    key = input("  粘贴 API Key (或按回车跳过): ").strip()
    if key and key.startswith("wrk-"):
        env_path = PROJECT_ROOT / "config" / ".env"
        env_path.parent.mkdir(exist_ok=True)
        env_path.write_text(f"WEREAD_API_KEY={key}\n")
        os.chmod(env_path, 0o600)
        print(f"  ✅ 已保存到 config/.env (权限 600)")
    else:
        print("  ⚠️  跳过, 请手动设置: export WEREAD_API_KEY='wrk-...'")
    print()
    print("Step 3: 首次同步")
    print("  python src/weread_sync.py")
    print()
    print("Step 4: 设置定时任务 (每小时自动同步)")
    print("  crontab -e")
    print("  添加: 7 * * * * cd /path/to/WRS001 && python src/weread_sync.py --incremental")
    print()
    print("完成! 笔记将同步到 output/ 目录, 可直接用 Obsidian 打开。")


def main():
    parser = argparse.ArgumentParser(description="WeReadSync — 微信读书笔记 → Markdown")
    parser.add_argument("--incremental", action="store_true", help="增量同步 (跳过未变化)")
    parser.add_argument("--output", type=str, default="", help="输出目录 (默认: output/)")
    parser.add_argument("--setup", action="store_true", help="交互式安装向导")
    parser.add_argument("--cleanup", action="store_true", help="清理已删除书籍的旧文件")
    args = parser.parse_args()

    if args.setup:
        cmd_setup()
        return

    key = load_api_key()
    syncer = WeReadSync(key, output_dir=args.output)

    if args.cleanup:
        removed = syncer.cleanup_stale()
        print(f"Cleanup: removed {removed} stale files")
        return

    start = time.time()
    result = syncer.sync_all(incremental=args.incremental)

    elapsed = time.time() - start
    print(f"\nSync complete: {result.get('synced', 0)} updated, "
          f"{result.get('skipped', 0)} unchanged (total {result.get('total', 0)} books)")
    print(f"Time: {elapsed:.1f}s | Output: {syncer._output}")
    print(f"Obsidian-ready: open '{syncer._output}' as vault folder")


if __name__ == "__main__":
    main()
