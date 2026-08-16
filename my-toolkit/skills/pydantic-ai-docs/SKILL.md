---
name: pydantic-ai-docs
description: Search and quote the official Pydantic AI documentation at pydantic.dev/docs/ai instead of answering from memory. Use this whenever a question or task touches Pydantic AI (the `pydantic-ai` / `pydantic_ai` Python package) — Agent construction, output types and structured output, function tools and toolsets, dependencies and RunContext, message history, streaming and event handlers, model and provider setup (OpenAI, Anthropic, Google, Bedrock, Groq, Ollama, the Gateway), MCP servers, retries and ModelRetry, durable execution (Temporal, DBOS, Prefect), evals with pydantic-evals, Logfire instrumentation, the AG-UI/A2A/CLI interfaces, realtime voice, embeddings, or the Pydantic AI harness (memory, subagents, coding agent). Trigger it for phrasings like "how do I do X in pydantic-ai", "why is my agent...", "what's the type of...", an ImportError or AttributeError from `pydantic_ai`, any question naming a Pydantic AI class, decorator, or keyword argument, and any request to write or debug code that imports `pydantic_ai` — even when you think you already know the answer, because Pydantic AI ships frequently, went through a V1→V2 API break, and recalled details are often stale.
---

# Pydantic AI documentation search

Pydantic AI moves fast and went through a V1 → V2 rename that shifted class names,
imports, and keyword arguments. Writing `pydantic_ai` code from memory is how you end up
with an import that no longer resolves or a parameter that was renamed two releases ago.
The docs are the source of truth, the whole corpus is cached locally, and searching it
takes about a second — so search first and quote what you find.

The docs publish an index of all 259 pages plus a single file containing every page's
markdown, so the bundled script pulls one ~5 MB download and then answers offline.

## The script

`pydantic-ai-docs` is a launcher in the plugin's `bin/`, which Claude Code puts on **the
Bash tool's** PATH — so it runs from any working directory and you never need to know
where the plugin lives. That PATH injection covers the Bash tool only. From the PowerShell
tool the bare command is not found; use the direct invocation below instead.

```bash
pydantic-ai-docs search <terms...>            # rank pages by title/slug — instant
pydantic-ai-docs grep <regex>                 # full-text search across every page
pydantic-ai-docs read <slug> --outline        # a page's headings, cheap
pydantic-ai-docs read <slug> --section <re>   # just the sections you need
pydantic-ai-docs read <slug>                  # the whole page
pydantic-ai-docs index                        # list all pages, for browsing
```

If the shell reports the command isn't found — you're in the PowerShell tool, or the
plugin was installed after this session started — call the script directly. The script
locates its own cache relative to itself, so any absolute path works.

**Always quote the path.** Plugin roots routinely contain spaces, and a marketplace
installed from a directory can contain `&`, `(`, or `'` too — all of which break an
unquoted command in both shells. Quote it even when the current path looks harmless:

```bash
python "<plugin-root>/skills/pydantic-ai-docs/scripts/docs.py" search <terms...>
```

```powershell
& python "<plugin-root>\skills\pydantic-ai-docs\scripts\docs.py" search <terms...>
```

`<plugin-root>` is available to hooks as `${CLAUDE_PLUGIN_ROOT}`, but that variable is
*not* set in the Bash or PowerShell tool environment — substitute the literal path there.
The `bin/pydantic-ai-docs.cmd` shim works the same way from PowerShell, again quoted and
behind the `&` call operator.

Useful flags: `--api` includes the API-reference pages (excluded by default, see below),
`--slug <regex>` narrows `grep` to matching pages, `--context N` widens grep context lines,
`--limit N` caps results, `--json` for structured output, and `--refresh` bypasses the
cache when you suspect the docs just changed.

The corpus is cached under `~/.cache/pydantic-ai-docs` for 24 hours. The first `grep` or
`read` pulls ~5 MB (a few seconds); every call after that is instant.

## How to answer a question

**Reach for `grep` more than you would elsewhere.** Only 34 of the 186 guide pages carry a
description in the index, so `search` is really matching titles and slugs. It lands
conceptual questions ("agents", "toolsets", "durable execution") but it cannot find a
symbol. Anything that names a class, decorator, exception, or keyword argument belongs in
`grep`, where the page bodies are:

```bash
pydantic-ai-docs search output structured
pydantic-ai-docs grep 'output_type' --context 3
pydantic-ai-docs grep '@agent\.tool' --slug 'tools'
```

**Then read the section, not the page.** Guide pages here are long — `core-concepts/agent`
alone is ~1800 lines, and reading it whole costs far more context than the answer is worth.
`--outline` gives you the headings for a few hundred tokens, and `--section` pulls only what
you name:

```bash
pydantic-ai-docs read core-concepts/agent --outline
pydantic-ai-docs read core-concepts/agent --section 'streaming|iterating'
```

**The API reference is hidden by default, on purpose.** 73 of the 259 pages are generated
`pydantic_ai.*` reference — signature dumps that would swamp every result for a common word
like "model" or "tool". Add `--api` when you actually want a signature, a full parameter
list, or an exception's definition; leave it off when you want to understand a concept.
`read` already prefers the guide over the same-named reference page, so `read agent` gets
you the concept page and `read api/pydantic-ai/agent` gets you the module. Passing `--slug`
to `grep` overrides the exclusion — you named the pages, so it searches them whether or not
they're reference — which makes `--slug 'api/'` the quick way to search signatures alone.

**Cross-check when the answer sounds surprising.** If a guide shows one API shape and you
remember another, grep for the symbol across everything with `--api` — the guide and the
reference sometimes describe different points in the V1 → V2 transition, and
`overview/migration` (the V1 → V2 migration map) resolves which is current.

## Reporting what you found

Quote the docs rather than paraphrasing from memory, and cite the human-readable URL —
`https://pydantic.dev/docs/ai/core-concepts/agent/` — which the script already prints for
you. Run any code you write against what the docs show, not against remembered signatures.

Two things worth flagging to the user when they show up:

- **V1 vs V2.** If a symbol changed names or moved modules, say so and point at
  `overview/migration`. A user on V1 following V2 docs gets an ImportError with no
  explanation attached.
- **Preview and beta markers.** Parts of the harness and realtime surface are explicitly
  marked as unstable in the docs. Pass that caveat along rather than presenting the
  behavior as settled.

If the docs genuinely don't cover something, say so plainly instead of filling the gap with
a plausible-sounding guess. "The docs don't document this; here's the closest thing they do
cover" is a more useful answer than an invented keyword argument.

## Docs describe intent; the installed version is the fact

The docs describe the current release. When the question is "why doesn't *my* code work",
the docs give you the correct shape and the local install gives you the discrepancy: check
`pip show pydantic-ai` (or `uv pip show`) for the installed version, and read the actual
signature with `python -c "import pydantic_ai, inspect; print(inspect.signature(...))"`.
A doc page and a live traceback disagreeing is usually a version gap, not a doc error.

## Fetching pages by hand

You shouldn't need to — the cached corpus is complete, all 259 pages — but if you do fetch
a page directly, use the `index.md` form exactly as it appears in `llms.txt`:
`https://pydantic.dev/docs/ai/core-concepts/agent/index.md`. A bare `agent.md` does **not**
404; it silently redirects to the HTML page and hands you 160 KB of markup instead of docs.

The docs ask agents to pass `goal` and `organization` query parameters so maintainers can
see where agents get stuck; the script exposes them as `--goal` and `--organization`. These
go to an external service, so keep them to a short public task description and a public
company name — never anything private or confidential. Omitting them is fine.

## When the index itself fails

If `search` returns nothing and `grep --api` finds nothing, the topic may live outside these
docs. The coverage is wider than the name suggests — `evals/*` is a full ~25-page tree for
`pydantic-evals`, and Logfire integration has its own pages — so check `index` before
assuming a gap. What genuinely isn't here is core Pydantic validation (`BaseModel`,
validators, `Field`) and the Logfire product docs, which are separate sites.

The Logfire boundary is worth knowing precisely, because eval questions straddle it: `evals/*`
here documents the `pydantic-evals` *library* (`Case`, `Dataset`, `Evaluator`, `LLMJudge`), while
the Logfire *platform* side — hosted datasets, experiments and baselines, live evals, human review
queues — lives at `pydantic.dev/docs/logfire/evaluate/*` and belongs to the `logfire-docs` skill.
