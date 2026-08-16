#!/usr/bin/env python3
"""Search and read the official Pydantic AI documentation.

The docs publish two machine-readable files:

  https://pydantic.dev/docs/ai/llms.txt       index, `- [Title](url): description`
  https://pydantic.dev/docs/ai/llms-full.txt  every page's markdown, concatenated

The full corpus is one ~5 MB download covering all pages, so `grep` needs a single
fetch rather than a per-page crawl. Pages inside it are delimited by a `# [Title](url)`
heading, which is what lets a match be attributed back to its page.

Commands:
  index                     List every page (title + url + description).
  search <terms...>         Rank pages by title/description match. Cheap.
  read <slug|url|title> [--outline] [--section REGEX]
                            Print one page's markdown from the corpus. Pages run
                            past 1500 lines, so --outline lists its headings and
                            --section pulls just the matching ones.
  grep <regex> [--context N] [--slug PAT]
                            Full-text search across every page.

Flags: --refresh (ignore cache), --json, --limit N, --api (include API-reference
pages, which are excluded by default because they drown out the guides).

Stdlib only. Cache lives in ~/.cache/pydantic-ai-docs and expires after 24h.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

INDEX_URL = "https://pydantic.dev/docs/ai/llms.txt"
FULL_URL = "https://pydantic.dev/docs/ai/llms-full.txt"
CACHE = Path.home() / ".cache" / "pydantic-ai-docs"
TTL = 24 * 60 * 60
UA = "pydantic-ai-docs-skill/1.0"

# Index lines look like: `- [Agents](https://pydantic.dev/docs/ai/core-concepts/agent/index.md): desc`
ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)(?::\s*(?P<desc>.*))?$")
# Inside llms-full.txt each page opens with `# [Title](human-url)`.
PAGE_RE = re.compile(r"^# \[(?P<title>[^\]]*)\]\((?P<url>https?://[^)]+)\)\s*$")
HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*)$")


def fetch(url: str, goal: str | None = None, organization: str | None = None) -> str:
    # The docs ask agents to pass `goal` and `organization` so maintainers can see
    # where agents get stuck. These go to an external service — keep them to a short
    # public task description, never anything private.
    params = {k: v for k, v in (("goal", goal), ("organization", organization)) if v}
    if params:
        sep = "&" if "?" in url else "?"
        url = url + sep + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def cached(key: str, url: str, refresh: bool, goal: str | None, organization: str | None) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / key
    if not refresh and path.exists() and time.time() - path.stat().st_mtime < TTL:
        return path.read_text(encoding="utf-8")
    text = fetch(url, goal, organization)
    path.write_text(text, encoding="utf-8")
    return text


def slug_of(url: str) -> str:
    """https://pydantic.dev/docs/ai/core-concepts/agent/index.md -> core-concepts/agent"""
    tail = url.split("/docs/ai/", 1)[-1]
    tail = tail.removesuffix("index.md").removesuffix(".md")
    return tail.strip("/")


def human_url(url: str) -> str:
    """The index.md URL is for machines; cite the page a human can open."""
    return url.removesuffix("index.md") if url.endswith("index.md") else url


def is_api(slug: str) -> bool:
    return slug.startswith("api/")


def load_index(refresh: bool, goal: str | None, org: str | None) -> list[dict]:
    text = cached("llms.txt", INDEX_URL, refresh, goal, org)
    entries, seen = [], set()
    for line in text.splitlines():
        m = ENTRY_RE.match(line.strip())
        if not m:
            continue
        url = m["url"]
        slug = slug_of(url)
        if slug in seen:
            continue
        seen.add(slug)
        entries.append(
            {
                "title": m["title"],
                "url": url,
                "slug": slug,
                "description": (m["desc"] or "").strip(),
            }
        )
    if not entries:
        sys.exit("Could not parse any entries from llms.txt — its format may have changed.")
    return entries


def load_corpus(refresh: bool, goal: str | None, org: str | None) -> dict[str, dict]:
    """Split llms-full.txt into pages keyed by slug.

    One download covers every page, so this is the only network call `grep` and
    `read` ever need.
    """
    text = cached("llms-full.txt", FULL_URL, refresh, goal, org)
    pages: dict[str, dict] = {}
    current: dict | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = PAGE_RE.match(line)
        if m:
            if current:
                current["lines"] = buf
                pages[current["slug"]] = current
            url = m["url"]
            current = {"title": m["title"], "url": url, "slug": slug_of(url)}
            buf = []
            continue
        if current:
            buf.append(line)
    if current:
        current["lines"] = buf
        pages[current["slug"]] = current
    if not pages:
        sys.exit("Could not split llms-full.txt into pages — its format may have changed.")
    return pages


def extract_sections(lines: list[str], pattern: str) -> list[str]:
    """Return every `##`+ section whose heading matches, through to the next heading
    at the same or shallower depth. The guide pages run past 1500 lines, so pulling
    one section is usually the difference between an answer and a context dump."""
    pat = re.compile(pattern, re.I)
    out: list[str] = []
    depth: int | None = None
    for line in lines:
        m = HEADING_RE.match(line)
        if m:
            level = len(m["hashes"])
            if depth is not None and level <= depth:
                depth = None
            if depth is None and level >= 2 and pat.search(m["text"]):
                depth = level
        if depth is not None:
            out.append(line)
    return out


def resolve(target: str, entries: list[dict]) -> dict | None:
    """Accept a slug, a full URL, or a unique title/slug substring."""
    t = target.strip()
    if t.startswith("http"):
        t = slug_of(t)
    t = t.removesuffix("index.md").removesuffix(".md").strip("/").lower()
    for e in entries:
        if e["slug"].lower() == t:
            return e
    # A bare leaf name ('agent', 'anthropic') is how people actually refer to pages.
    # At each widening step prefer a guide over the API-reference page of the same
    # name — asking to read 'agent' means the concept page, not pydantic_ai.agent.
    for candidates in (
        [e for e in entries if e["slug"].lower().rsplit("/", 1)[-1] == t],
        [e for e in entries if t in e["slug"].lower() or t in e["title"].lower()],
    ):
        if len(candidates) == 1:
            return candidates[0]
        guides = [e for e in candidates if not is_api(e["slug"])]
        if len(guides) == 1:
            return guides[0]
    return None


def score(entry: dict, terms: list[str]) -> int:
    """Slug matches outrank title, title outranks description — doc slugs are the
    names people use ('agent', 'toolsets', 'anthropic')."""
    title = entry["title"].lower()
    desc = entry["description"].lower()
    slug = entry["slug"].lower()
    total = 0
    for term in terms:
        if term == slug.rsplit("/", 1)[-1]:
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
    # The docs use arrows, em dashes and box-drawing characters. On a Windows console
    # defaulting to cp1252 those raise UnicodeEncodeError mid-print, so force UTF-8
    # out and degrade gracefully if the terminal can't render a glyph.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    # Global flags live on a parent parser as well as the top level, so both
    # `docs.py --json index` and `docs.py index --json` work. Getting that wrong is
    # an easy way to lose a minute to an argparse error mid-lookup.
    def add_common(p, suppress: bool) -> None:
        # On the subparsers the defaults are SUPPRESSed: without that, a subparser
        # re-declaring --api would overwrite a top-level `--api` back to False.
        d = {"default": argparse.SUPPRESS} if suppress else {}
        p.add_argument("--refresh", action="store_true", help="bypass the 24h cache", **d)
        p.add_argument("--json", action="store_true", dest="as_json", **d)
        p.add_argument("--api", action="store_true", help="include api/* reference pages", **d)
        p.add_argument("--goal", help="short public description of what you're looking up", **d)
        p.add_argument("--organization", help="public org name, if known", **d)

    common = argparse.ArgumentParser(add_help=False)
    add_common(common, suppress=True)

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common(ap, suppress=False)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index", parents=[common])

    p_search = sub.add_parser("search", parents=[common])
    p_search.add_argument("terms", nargs="+")
    p_search.add_argument("--limit", type=int, default=10)

    p_read = sub.add_parser("read", parents=[common])
    p_read.add_argument("target")
    p_read.add_argument("--section", help="only print `##`+ sections whose heading matches this regex")
    p_read.add_argument("--outline", action="store_true", help="list the page's headings instead of its body")

    p_grep = sub.add_parser("grep", parents=[common])
    p_grep.add_argument("pattern")
    p_grep.add_argument("--context", type=int, default=2)
    p_grep.add_argument("--slug", help="only search pages whose slug matches this regex")
    p_grep.add_argument("--limit", type=int, default=60, help="max matching lines to print")

    args = ap.parse_args()
    goal, org = args.goal, args.organization
    entries = load_index(args.refresh, goal, org)
    visible = entries if args.api else [e for e in entries if not is_api(e["slug"])]

    if args.cmd == "index":
        emit(visible, args.as_json, lambda e: f"{e['slug']:<45} {e['title']}\n{'':<45} {e['description']}")
        hidden = len(entries) - len(visible)
        note = f"\n{len(visible)} pages" + (f" ({hidden} api/* pages hidden; --api to show)." if hidden else ".")
        print(note, file=sys.stderr)
        return

    if args.cmd == "search":
        terms = [t.lower() for t in args.terms]
        ranked = sorted(((score(e, terms), e) for e in visible), key=lambda p: -p[0])
        hits = [dict(e, score=s) for s, e in ranked if s > 0][: args.limit]
        if not hits:
            print("No title/description match. Try `grep` for a full-text search, "
                  "`--api` to include the API reference, or `index` to browse.", file=sys.stderr)
            return
        emit(
            hits,
            args.as_json,
            lambda e: f"[{e['score']:>3}] {e['slug']}\n      {e['title']}\n      {e['description']}\n      {human_url(e['url'])}",
        )
        return

    pages = load_corpus(args.refresh, goal, org)

    if args.cmd == "read":
        entry = resolve(args.target, entries)
        if not entry:
            sys.exit(f"No single page matches {args.target!r}. Run `search` or `index` to find the slug.")
        page = pages.get(entry["slug"])
        if page is None:
            # Corpus and index disagree — fall back to the page's own markdown URL.
            print(f"<!-- {entry['title']} — {human_url(entry['url'])} (fetched directly) -->\n")
            print(fetch(entry["url"], goal, org))
            return
        print(f"<!-- {entry['title']} — {human_url(entry['url'])} -->\n")
        lines = page["lines"]
        if args.outline:
            for line in lines:
                if HEADING_RE.match(line):
                    print(line)
            return
        if args.section:
            body = extract_sections(lines, args.section)
            if not body:
                sys.exit(f"No heading on {entry['slug']} matches {args.section!r}. "
                         f"Run `read {entry['slug']} --outline` to see the headings.")
            print("\n".join(body).strip())
            return
        print("\n".join(lines).strip())
        return

    if args.cmd == "grep":
        pat = re.compile(args.pattern, re.I)
        slug_pat = re.compile(args.slug, re.I) if args.slug else None
        shown = 0
        for slug in sorted(pages):
            if slug_pat and not slug_pat.search(slug):
                continue
            if not args.api and not slug_pat and is_api(slug):
                continue
            page = pages[slug]
            lines = page["lines"]
            header_printed = False
            for i, line in enumerate(lines):
                if not pat.search(line):
                    continue
                if shown >= args.limit:
                    print(f"\n(stopped at {args.limit} matches — narrow the pattern or use --slug)",
                          file=sys.stderr)
                    return
                shown += 1
                if not header_printed:
                    # One header per page keeps a dense page from burying its own hits.
                    print(f"\n=== {slug} :: {human_url(page['url'])} ===")
                    header_printed = True
                lo, hi = max(0, i - args.context), min(len(lines), i + args.context + 1)
                for j in range(lo, hi):
                    print(f"{j + 1:>5}{'>' if j == i else ' '} {lines[j]}")
                print()
        if shown == 0:
            print("No full-text match." + ("" if args.api else " The API reference was excluded — retry with --api."),
                  file=sys.stderr)


if __name__ == "__main__":
    main()
