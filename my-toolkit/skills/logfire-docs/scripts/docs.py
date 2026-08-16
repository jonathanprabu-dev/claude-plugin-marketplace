#!/usr/bin/env python3
"""Search and read the official Pydantic Logfire documentation.

The docs publish two machine-readable files:

  https://pydantic.dev/docs/logfire/llms.txt       index, `- [Title](url): description`
  https://pydantic.dev/docs/logfire/llms-full.txt  every page's markdown, concatenated

The full corpus is one ~2 MB download covering every page, so `grep` needs a single
fetch rather than a per-page crawl. Pages inside it are delimited by a `# [Title](url)`
heading, which is what lets a match be attributed back to its page.

The index also groups entries under `##`/`###` headings ("Evaluations", "Integrations",
"Reference & Resources"). Those are recorded per entry, because Logfire slugs end in
generic leaf names — `overview` exists under evaluate/ and cookbook/ both — and the
section is what tells them apart in a result list.

Commands:
  index [--group REGEX]     List every page (section + title + url + description).
  search <terms...>         Rank pages by slug/title/description match. Cheap.
  read <slug|url|title> [--outline] [--section REGEX]
                            Print one page's markdown from the corpus. Pages run
                            long, so --outline lists its headings and --section
                            pulls just the matching ones.
  grep <regex> [--context N] [--slug PAT] [--group PAT]
                            Full-text search across every page.

Flags: --refresh (ignore cache), --json, --limit N, --group REGEX (restrict to
index sections), --goal / --organization (see fetch()).

Stdlib only. Cache lives in ~/.cache/logfire-docs and expires after 24h.
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

INDEX_URL = "https://pydantic.dev/docs/logfire/llms.txt"
FULL_URL = "https://pydantic.dev/docs/logfire/llms-full.txt"
CACHE = Path.home() / ".cache" / "logfire-docs"
TTL = 24 * 60 * 60
UA = "logfire-docs-skill/1.0"

# Index lines look like: `- [Overview](https://pydantic.dev/docs/logfire/evaluate/overview/index.md): desc`
ENTRY_RE = re.compile(r"^- \[(?P<title>[^\]]+)\]\((?P<url>[^)]+)\)(?::\s*(?P<desc>.*))?$")
# ...grouped under `## Section` / `### Subsection` headings. `#` alone is the doc title.
SECTION_RE = re.compile(r"^(?P<hashes>#{2,4})\s+(?P<text>.+?)\s*$")
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
    """https://pydantic.dev/docs/logfire/evaluate/overview/index.md -> evaluate/overview

    llms-full.txt cites the same pages without the `index.md` tail, so both forms
    have to reduce to the same slug or the index and the corpus won't line up.
    """
    tail = url.split("/docs/logfire/", 1)[-1]
    tail = tail.removesuffix("index.md").removesuffix(".md")
    return tail.strip("/")


def human_url(url: str) -> str:
    """The index.md URL is for machines; cite the page a human can open."""
    return url.removesuffix("index.md") if url.endswith("index.md") else url


def load_index(refresh: bool, goal: str | None, org: str | None) -> list[dict]:
    text = cached("llms.txt", INDEX_URL, refresh, goal, org)
    entries, seen = [], set()
    # Track the heading stack so each entry knows the section it was listed under;
    # `### Evaluations` nested in `## AI Engineering` becomes "AI Engineering > Evaluations".
    stack: dict[int, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        m = ENTRY_RE.match(line)
        if not m:
            h = SECTION_RE.match(line)
            if h:
                level = len(h["hashes"])
                stack = {k: v for k, v in stack.items() if k < level}
                stack[level] = h["text"]
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
                "section": " > ".join(stack[k] for k in sorted(stack)),
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


def resolve(target: str, entries: list[dict]) -> tuple[dict | None, list[dict]]:
    """Accept a slug, a full URL, or a title/slug substring.

    Returns (entry, candidates). Leaf names in these docs are heavily reused —
    `overview` alone names half a dozen pages — so an ambiguous target comes back
    as a candidate list to show the caller rather than an arbitrary pick.
    """
    t = target.strip()
    if t.startswith("http"):
        t = slug_of(t)
    t = t.removesuffix("index.md").removesuffix(".md").strip("/").lower()
    for e in entries:
        if e["slug"].lower() == t:
            return e, []
    # A bare leaf name ('live-evals', 'manage-datasets') is how people refer to pages;
    # widen only if the exact-leaf pass didn't settle it.
    for candidates in (
        [e for e in entries if e["slug"].lower().rsplit("/", 1)[-1] == t],
        [e for e in entries if t in e["slug"].lower() or t in e["title"].lower()],
    ):
        if len(candidates) == 1:
            return candidates[0], []
        if candidates:
            return None, candidates
    return None, []


def score(entry: dict, terms: list[str]) -> int:
    """Slug matches outrank title, title outranks description — doc slugs are the
    names people use ('evaluate', 'live-evals', 'datasets').

    The section counts too, and it earns its weight here: Logfire reuses leaf names
    across the tree, so 'evals overview' would tie several `overview` pages without
    the "Evaluations" section breaking it toward the right one.
    """
    title = entry["title"].lower()
    desc = entry["description"].lower()
    slug = entry["slug"].lower()
    section = entry.get("section", "").lower()
    total = 0
    for term in terms:
        if term == slug.rsplit("/", 1)[-1]:
            total += 12
        elif term in slug:
            total += 6
        if term in title:
            total += 4
        if term in section:
            total += 3
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
        # re-declaring --group would overwrite a top-level `--group` back to None.
        d = {"default": argparse.SUPPRESS} if suppress else {}
        p.add_argument("--refresh", action="store_true", help="bypass the 24h cache", **d)
        p.add_argument("--json", action="store_true", dest="as_json", **d)
        p.add_argument("--group", help="only pages whose index section matches this regex", **d)
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
    if args.group:
        gpat = re.compile(args.group, re.I)
        visible = [e for e in entries if gpat.search(e["section"])]
        if not visible:
            sections = sorted({e["section"] for e in entries})
            sys.exit(f"No index section matches {args.group!r}. Sections are:\n  " + "\n  ".join(sections))
    else:
        visible = entries

    if args.cmd == "index":
        emit(
            visible,
            args.as_json,
            lambda e: f"{e['slug']:<45} {e['title']}\n{'':<45} [{e['section']}] {e['description']}",
        )
        print(f"\n{len(visible)} of {len(entries)} pages.", file=sys.stderr)
        return

    if args.cmd == "search":
        terms = [t.lower() for t in args.terms]
        ranked = sorted(((score(e, terms), e) for e in visible), key=lambda p: -p[0])
        hits = [dict(e, score=s) for s, e in ranked if s > 0][: args.limit]
        if not hits:
            print("No slug/title/description match. Try `grep` for a full-text search, "
                  "or `index` to browse.", file=sys.stderr)
            return
        emit(
            hits,
            args.as_json,
            lambda e: f"[{e['score']:>3}] {e['slug']}  ({e['section']})\n      {e['title']}\n"
                      f"      {e['description']}\n      {human_url(e['url'])}",
        )
        return

    pages = load_corpus(args.refresh, goal, org)

    if args.cmd == "read":
        entry, candidates = resolve(args.target, visible)
        if not entry:
            if candidates:
                listing = "\n  ".join(f"{e['slug']:<40} ({e['section']})" for e in candidates[:15])
                sys.exit(f"{args.target!r} matches {len(candidates)} pages — pick one:\n  {listing}")
            sys.exit(f"No page matches {args.target!r}. Run `search` or `index` to find the slug.")
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
        in_group = {e["slug"] for e in visible} if args.group else None
        shown = 0
        for slug in sorted(pages):
            if slug_pat and not slug_pat.search(slug):
                continue
            if in_group is not None and slug not in in_group:
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
            hint = " (--slug/--group narrowed the corpus; drop them to search everything)" if (slug_pat or in_group) else ""
            print(f"No full-text match.{hint}", file=sys.stderr)


if __name__ == "__main__":
    main()
