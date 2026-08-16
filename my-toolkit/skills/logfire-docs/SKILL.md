---
name: logfire-docs
description: Search and quote the official Pydantic Logfire documentation at pydantic.dev/docs/logfire instead of answering from memory. Use this whenever a question or task touches Logfire — and especially its evaluation stack: datasets and experiments, offline evals with pydantic-evals, live/online evals scoring production traffic, evaluators and LLM judges, review of experiment runs, human review and annotation queues, the datasets SDK. It also covers the rest of the platform — `logfire.configure()`, spans and instrumentation, the Python/TypeScript/Rust SDKs, framework and LLM integrations, the live view, dashboards, alerts, SQL querying, prompt management, feature flags, tokens and environments, self-hosting. Trigger it for phrasings like "how do I evaluate my agent", "why is my eval score...", "set up an LLM judge", "compare this run against a baseline", "how do I send traces to Logfire", any question naming a Logfire UI screen, SDK function, or dataset/experiment concept, and any request to write or debug code that imports `logfire` or `pydantic_evals` — even when you think you already know the answer, because Logfire's eval surface is new, ships frequently, and recalled details are usually stale or invented.
---

# Pydantic Logfire documentation search

Logfire's evaluation surface — hosted datasets, experiments, live evals, annotation queues — is
recent and still moving, and much of it is *product* behavior rather than library API: which
button records a verdict, how an experiment gets compared against a baseline, what a hide rule
does to telemetry. None of that can be inferred from a function signature, and answering it from
memory produces confident descriptions of screens that don't exist. The docs are the source of
truth, the whole corpus is cached locally, and searching it takes about a second — so search
first and quote what you find.

The docs publish an index of all 269 pages plus a single file containing every page's markdown,
so the bundled script pulls one ~2 MB download and then answers offline.

## The script

`logfire-docs` is a launcher in the plugin's `bin/`, which Claude Code puts on **the Bash tool's**
PATH — so it runs from any working directory and you never need to know where the plugin lives.
That PATH injection covers the Bash tool only. From the PowerShell tool the bare command is not
found; use the direct invocation below instead.

```bash
logfire-docs search <terms...>              # rank pages by slug/title/description — instant
logfire-docs grep <regex>                   # full-text search across every page
logfire-docs read <slug> --outline          # a page's headings, cheap
logfire-docs read <slug> --section <re>     # just the sections you need
logfire-docs read <slug>                    # the whole page
logfire-docs index --group Evaluations      # browse one section of the docs
```

If the shell reports the command isn't found — you're in the PowerShell tool, or the plugin was
installed after this session started — call the script directly. The script locates its own cache
relative to itself, so any absolute path works.

**Always quote the path.** Plugin roots routinely contain spaces, and a marketplace installed from
a directory can contain `&`, `(`, or `'` too — all of which break an unquoted command in both
shells. Quote it even when the current path looks harmless:

```bash
python "<plugin-root>/skills/logfire-docs/scripts/docs.py" search <terms...>
```

```powershell
& python "<plugin-root>\skills\logfire-docs\scripts\docs.py" search <terms...>
```

`<plugin-root>` is available to hooks as `${CLAUDE_PLUGIN_ROOT}`, but that variable is *not* set
in the Bash or PowerShell tool environment — substitute the literal path there. The
`bin/logfire-docs.cmd` shim works the same way from PowerShell, again quoted and behind the `&`
call operator.

Useful flags: `--group <regex>` restricts everything to an index section, `--slug <regex>` narrows
`grep` to matching pages, `--context N` widens grep context lines, `--limit N` caps results,
`--json` for structured output, and `--refresh` bypasses the cache when you suspect the docs just
changed.

The corpus is cached under `~/.cache/logfire-docs` for 24 hours. The first `grep` or `read` pulls
~2 MB (a couple of seconds); every call after that is instant.

## How to answer a question

**Narrow by section early.** Every index entry carries the heading it was listed under, and the
eval material is all under `AI Engineering > Evaluations` (9 pages, slugs `evaluate/*`). Passing
`--group Evaluations` keeps a search for a generic word like "dataset" or "score" from returning
the TypeScript SDK page and the API reference alongside the page you wanted:

```bash
logfire-docs index --group Evaluations
logfire-docs search datasets experiments --group Evaluations
```

Drop the filter when the question crosses the boundary — "how do I evaluate my agent" usually also
touches instrumentation and the cookbook — because the section split is editorial, not a wall.

**Use `search` for concepts, `grep` for symbols.** Descriptions are rich here, so `search` lands
conceptual questions well. But titles and descriptions won't contain `push_dataset`,
`report_evaluators`, or `LOGFIRE_TOKEN` — page bodies will:

```bash
logfire-docs search live evals monitoring
logfire-docs grep 'push_dataset' --context 3
logfire-docs grep 'LLMJudge' --group Evaluations
```

**Then read the section, not the page.** `--outline` gives you a page's headings for a few hundred
tokens, and `--section` pulls only what you name — worth doing by reflex, since spending a whole
page of context to answer one question is the most common way this skill gets expensive:

```bash
logfire-docs read evaluate/overview --outline
logfire-docs read evaluate/live-evals --section 'investigate|hide'
```

**Leaf names repeat, so `read` may ask you to disambiguate.** `overview` names pages under both
`evaluate/` and `deploy/`. When `read` reports multiple matches it prints the candidates with
their sections — pick the slug rather than guessing.

**The docs lean on screenshots for UI workflows.** Eval pages describe the interface in prose and
then show it: `![...](/docs/logfire/images/live-evaluations-target-detail.png)`. The image alt text
survives into the markdown and is often the most precise description of what's on screen, so quote
it — and when a user is trying to find a control, cite the page URL so they can see the picture.

## Reporting what you found

Quote the docs rather than paraphrasing from memory, and cite the human-readable URL —
`https://pydantic.dev/docs/logfire/evaluate/overview/` — which the script already prints for you.
Run any code you write against what the docs show, not against remembered signatures.

Two things worth flagging to the user when they show up:

- **Hosted vs code-defined datasets.** Much of the eval surface exists in two forms — a dataset
  curated in the Logfire UI, and one defined in Python and pushed. Advice that's right for one is
  often wrong for the other, so say which one you're describing and check which the user has.
- **Product behavior that isn't reversible.** Things like hide rules, retired evaluators, and
  pushes that overwrite hosted values have documented consequences. Pass those along; the docs
  state them plainly and users generally haven't read that far.

If the docs genuinely don't cover something, say so plainly instead of filling the gap with a
plausible-sounding guess. "The docs don't document this; here's the closest thing they do cover"
is a more useful answer than an invented method name.

## Docs describe intent; the installed version is the fact

The docs describe the current release. When the question is "why doesn't *my* code work", the docs
give you the correct shape and the local install gives you the discrepancy: check
`pip show logfire pydantic-evals` (or `uv pip show`) for installed versions, and read the actual
signature with `python -c "import logfire, inspect; print(inspect.signature(...))"`. A doc page and
a live traceback disagreeing is usually a version gap, not a doc error.

## Fetching pages by hand

You shouldn't need to — the cached corpus is complete, all 269 pages — but if you do fetch a page
directly, use the `index.md` form exactly as it appears in `llms.txt`:
`https://pydantic.dev/docs/logfire/evaluate/overview/index.md`.

The docs ask agents to pass `goal` and `organization` query parameters so maintainers can see where
agents get stuck; the script exposes them as `--goal` and `--organization`. These go to an external
service, so keep them to a short public task description and a public company name — never anything
private or confidential. Omitting them is fine.

## Where the coverage stops

If `search` returns nothing and `grep` finds nothing, the topic likely lives in a neighbouring set
of docs. The split that matters most for eval questions:

- **The Logfire platform** — hosted datasets, experiments and their comparison, live/online evals,
  human review and annotation queues, the datasets SDK (`LogfireAPIClient`, `push_dataset`) — is
  documented **here**, under `evaluate/*`.
- **The `pydantic-evals` library itself** — `Case`, `Dataset`, `Evaluator`, `EvaluatorContext`,
  `LLMJudge`, `evaluate()`, the report objects — is documented at `pydantic.dev/docs/ai/evals/*`,
  a different site. That's the **`pydantic-ai-docs` skill's** corpus, not this one. These docs
  show pydantic-evals in use and link to it, but they are not its API reference.

So "how do I write a custom evaluator class" is a pydantic-ai-docs question, while "why does my
experiment show no baseline to compare against" is this one. Questions about an agent that is both
instrumented and evaluated legitimately need both — check `cookbook/evaluate-an-agent`, which walks
the whole path end to end, before splitting the lookup.

Core Pydantic validation (`BaseModel`, validators, `Field`) is a third site again, and Claude Code
questions belong to `claude-code-docs`.
