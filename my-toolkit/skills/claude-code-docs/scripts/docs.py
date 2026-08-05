#!/usr/bin/env python3
"""Search and read the official Claude Code documentation.

The docs publish a machine-readable index at https://code.claude.com/docs/llms.txt
listing every page as `- [Title](url.md): description`. Every page is also served
as raw markdown at its `.md` URL, so no HTML parsing is needed anywhere.

Commands:
  index                     List every page (title + url + description).
  search <terms...>         Rank pages by title/description match. Instant, no downloads.
  read <slug|url>           Print one page's raw markdown.
  grep <regex> [--context N] [--slug PAT]
                            Full-text search across every page. Downloads the corpus
                            once into a local cache, then it is instant.

Flags: --refresh (ignore cache), --json, --limit N.
Stdlib only. Cache lives in ~/.cache/claude-code-docs and expires after 24h.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

INDEX_URL = "https://code.claude.com/docs/llms.txt"
BASE = "https://code.claude.com/docs/en/"
CACHE = Path.home() / ".cache" / "claude-code-docs"
TTL = 24 * 60 * 60
UA = "claude-code-docs-skill/1.0"

ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)(?::\s*(?P<desc>.*))?$")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def cached(key: str, url: str, refresh: bool) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / key
    if not refresh and path.exists() and time.time() - path.stat().st_mtime < TTL:
        return path.read_text(encoding="utf-8")
    text = fetch(url)
    path.write_text(text, encoding="utf-8")
    return text


def slug_of(url: str) -> str:
    """en/agent-sdk/hooks.md -> agent-sdk/hooks"""
    return url.split("/docs/en/", 1)[-1].removesuffix(".md")


def human_url(url: str) -> str:
    """The .md URL is for machines; cite the page a human can open."""
    return url.removesuffix(".md")


def load_index(refresh: bool = False) -> list[dict]:
    text = cached("llms.txt", INDEX_URL, refresh)
    entries = []
    for line in text.splitlines():
        m = ENTRY_RE.match(line.strip())
        if not m:
            continue
        url = m["url"]
        entries.append(
            {
                "title": m["title"],
                "url": url,
                "slug": slug_of(url),
                "description": (m["desc"] or "").strip(),
            }
        )
    if not entries:
        sys.exit("Could not parse any entries from llms.txt — its format may have changed.")
    return entries


def resolve(target: str, entries: list[dict]) -> dict | None:
    """Accept a slug, a full URL (with or without .md), or a unique title substring."""
    t = target.strip()
    if t.startswith("http"):
        t = slug_of(t)
    t = t.removesuffix(".md").strip("/")
    for e in entries:
        if e["slug"] == t:
            return e
    partial = [e for e in entries if t.lower() in e["slug"].lower() or t.lower() in e["title"].lower()]
    return partial[0] if len(partial) == 1 else None


def page_text(entry: dict, refresh: bool = False) -> str:
    key = "page-" + entry["slug"].replace("/", "__") + ".md"
    return cached(key, entry["url"], refresh)


def corpus(entries: list[dict], refresh: bool, slug_filter: str | None) -> dict[str, str]:
    """Download every page in parallel, reusing cache. First run takes ~20s."""
    targets = entries
    if slug_filter:
        pat = re.compile(slug_filter, re.I)
        targets = [e for e in entries if pat.search(e["slug"])]
    out: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(page_text, e, refresh): e for e in targets}
        for fut in concurrent.futures.as_completed(futures):
            e = futures[fut]
            try:
                out[e["slug"]] = fut.result()
            except (urllib.error.URLError, OSError) as exc:
                print(f"warning: could not fetch {e['slug']}: {exc}", file=sys.stderr)
    return out


def score(entry: dict, terms: list[str]) -> int:
    """Title matches outrank description matches; slug matches are a strong signal
    because doc slugs are the names people actually use ('hooks', 'mcp', 'settings')."""
    title = entry["title"].lower()
    desc = entry["description"].lower()
    slug = entry["slug"].lower()
    total = 0
    for term in terms:
        if term == slug.split("/")[-1]:
            total += 12
        elif term in slug:
            total += 6
        if term in title:
            total += 4
        total += min(desc.count(term), 3) * 2
    return total


def emit(rows: list[dict], as_json: bool, fmt) -> None:
    if as_json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(fmt(row))


def main() -> None:
    # Docs are full of arrows, em dashes and box-drawing characters. On a Windows
    # console defaulting to cp1252 those raise UnicodeEncodeError mid-print, so
    # force UTF-8 out and degrade gracefully if the terminal can't render a glyph.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="bypass the 24h cache")
    ap.add_argument("--json", action="store_true", dest="as_json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index")

    p_search = sub.add_parser("search")
    p_search.add_argument("terms", nargs="+")
    p_search.add_argument("--limit", type=int, default=10)

    p_read = sub.add_parser("read")
    p_read.add_argument("target")

    p_grep = sub.add_parser("grep")
    p_grep.add_argument("pattern")
    p_grep.add_argument("--context", type=int, default=2)
    p_grep.add_argument("--slug", help="only search pages whose slug matches this regex")
    p_grep.add_argument("--limit", type=int, default=60, help="max matching lines to print")

    args = ap.parse_args()
    entries = load_index(args.refresh)

    if args.cmd == "index":
        emit(entries, args.as_json, lambda e: f"{e['slug']:<45} {e['title']}\n{'':<45} {e['description']}")
        print(f"\n{len(entries)} pages.", file=sys.stderr)
        return

    if args.cmd == "search":
        terms = [t.lower() for t in args.terms]
        ranked = sorted(((score(e, terms), e) for e in entries), key=lambda p: -p[0])
        hits = [dict(e, score=s) for s, e in ranked if s > 0][: args.limit]
        if not hits:
            print("No title/description match. Try `grep` for a full-text search, "
                  "or `index` to browse everything.", file=sys.stderr)
            return
        emit(
            hits,
            args.as_json,
            lambda e: f"[{e['score']:>3}] {e['slug']}\n      {e['title']}\n      {e['description']}\n      {human_url(e['url'])}",
        )
        return

    if args.cmd == "read":
        entry = resolve(args.target, entries)
        if not entry:
            sys.exit(f"No single page matches {args.target!r}. Run `search` or `index` to find the slug.")
        print(f"<!-- {entry['title']} — {human_url(entry['url'])} -->\n")
        print(page_text(entry, args.refresh))
        return

    if args.cmd == "grep":
        pat = re.compile(args.pattern, re.I)
        docs = corpus(entries, args.refresh, args.slug)
        by_slug = {e["slug"]: e for e in entries}
        shown = 0
        for slug in sorted(docs):
            lines = docs[slug].splitlines()
            for i, line in enumerate(lines):
                if not pat.search(line):
                    continue
                if shown >= args.limit:
                    print(f"\n(stopped at {args.limit} matches — narrow the pattern or use --slug)",
                          file=sys.stderr)
                    return
                shown += 1
                print(f"\n=== {slug} :: {human_url(by_slug[slug]['url'])} ===")
                lo, hi = max(0, i - args.context), min(len(lines), i + args.context + 1)
                for j in range(lo, hi):
                    print(f"{j + 1:>5}{'>' if j == i else ' '} {lines[j]}")
        if shown == 0:
            print("No full-text match.", file=sys.stderr)


if __name__ == "__main__":
    main()
