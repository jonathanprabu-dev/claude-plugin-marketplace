---
name: logfire-docs
description: Search and quote the official Pydantic Logfire and Pydantic Evals documentation — pydantic.dev/docs/logfire plus the pydantic-evals library reference at pydantic.dev/docs/ai/evals — instead of answering from memory. Use this whenever a question or task touches Logfire or evaluating an AI agent, and especially the evaluation stack end to end: hosted datasets and experiments, offline evals with pydantic-evals, live/online evals scoring production traffic, evaluators and LLM judges, custom or span-based evaluators, `Case`, `Dataset`, `Evaluator`, `EvaluatorContext`, `LLMJudge`, dataset serialization, review of experiment runs, human review and annotation queues, the datasets SDK. It also covers the rest of the platform — `logfire.configure()`, spans and instrumentation, the Python/TypeScript/Rust SDKs, framework and LLM integrations, the live view, dashboards, alerts, SQL querying, prompt management, feature flags, tokens and environments, self-hosting. Trigger it for phrasings like "how do I evaluate my agent", "why is my eval score...", "set up an LLM judge", "compare this run against a baseline", "how do I send traces to Logfire", any question naming a Logfire UI screen, SDK function, or dataset/experiment concept, and any request to write or debug code that imports `logfire` or `pydantic_evals` — even when you think you already know the answer, because Logfire's eval surface is new, ships frequently, and recalled details are usually stale or invented.
---

# Pydantic Logfire and Pydantic Evals documentation search

Logfire's evaluation surface — hosted datasets, experiments, live evals, annotation queues — is
recent and still moving, and much of it is *product* behavior rather than library API: which
button records a verdict, how an experiment gets compared against a baseline, what a hide rule
does to telemetry. None of that can be inferred from a function signature, and answering it from
memory produces confident descriptions of screens that don't exist. The docs are the source of
truth, the whole corpus is cached locally, and searching it takes about a second — so search
first and quote what you find.

**Two doc sites, one corpus.** Evaluation questions don't respect the split between them: the
Logfire platform documents hosted datasets, experiments and live evals under `evaluate/*`, while
the `pydantic-evals` library — `Case`, `Dataset`, `Evaluator`, `LLMJudge`, `evaluate()`, the
report objects — is documented on a different site under `evals/*`. Someone asking "why is my
LLM judge scoring everything zero" has no reason to know which half owns the answer, and the
common case (an agent that is both instrumented and evaluated) needs both. So the script indexes
both and one search crosses the boundary: 291 pages, 269 from Logfire and 22 from Pydantic Evals.

Each site publishes an index plus a single file containing every page's markdown. Corpora load
lazily, one site at a time, because a lookup that stays on one side shouldn't pay for the other.

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

The corpora are cached under `~/.cache/logfire-docs` for 24 hours. The first `grep` or `read` on
the Logfire side pulls ~2 MB, and the Pydantic Evals side ~5 MB; every call after that is instant.
`search` and `index` only need the two indexes, so they stay cheap regardless.

## How to answer a question

**Know which side of the split you're on.** Both sites carry eval material and the division is
consistent:

- **Platform, slugs `evaluate/*`, section `AI Engineering > Evaluations`** (9 pages) — hosted
  datasets, experiments and their comparison, live/online evals, human review and annotation
  queues, the datasets SDK (`LogfireAPIClient`, `push_dataset`).
- **Library, slugs `evals/*`, section `Pydantic Evals`** (22 pages) — `Case`, `Dataset`,
  `Evaluator`, `EvaluatorContext`, `LLMJudge`, custom and span-based evaluators, dataset
  serialization, concurrency, retries, case lifecycle hooks.

So "why does my experiment show no baseline to compare against" is `evaluate/*`, and "how do I
write a custom evaluator class" is `evals/*`. When you're unsure, don't guess — search without a
filter and let the ranking show you which side answers it.

**Narrow by section when a generic word would drag in the world.** Every index entry carries the
heading it was listed under, and that heading doubles as the source label, so `--group` picks a
side without a separate flag:

```bash
logfire-docs search datasets experiments --group Evaluations      # platform only
logfire-docs search dataset serialization --group "Pydantic Evals" # library only
logfire-docs search llm judge                                      # both, ranked
```

Without a filter, a word like "dataset" or "score" also returns the TypeScript SDK page and the
API reference. With one, you lose the other side entirely — which is the wrong trade for "how do
I evaluate my agent", a question that legitimately spans instrumentation, the library, and the
cookbook. Filter when the term is generic and you know the side; otherwise let both compete.

**The two sides describe the same words differently.** A "dataset" in `evaluate/*` is a hosted
object you curate in a UI; a `Dataset` in `evals/*` is a Python object you construct. An
"evaluator" is a configured target on the platform and a class you subclass in the library.
Answering from the wrong page produces advice that is coherent and useless, so name which one you
mean when you report back.

**When the question names both a code object and a screen, your first lookup must be unfiltered.**
"I built a `Dataset` in Python but my teammate edits the dataset in the UI" names a class *and* an
action someone takes in a browser; so does "my `LLMJudge` scores are fine locally but the
experiment shows nothing". That conjunction is the tell that the answer lives on both sides, and
it's exactly the case where scoping feels safest and is most wrong — the question *is* which side
owns what, so a filter picked before searching assumes away the thing being asked. This applies to
`search` as much as `grep`: `--group Evaluations` on a question mentioning `Dataset` returns a
confident, well-cited, half-right answer, which is worse than a slow one. Search wide first, let
both sides rank, and narrow only once you've seen which pages actually compete.

**Pydantic Evals index entries have no descriptions.** The Logfire index is richly described and
`search` lands conceptual questions on it well; the `evals/*` entries carry only a title and
section, so they score on slug and title alone. When a library question doesn't surface the page
you expected, go to `grep` sooner than you would on the Logfire side — the page bodies are dense
and well worth searching directly.

**Use `search` for concepts, `grep` for symbols.** No index carries `push_dataset`,
`EvaluatorContext`, `report_evaluators` or `LOGFIRE_TOKEN` in a title or description — page bodies
do. `--slug` is the cheapest way to keep a symbol search on one site, and it also means only that
site's corpus gets downloaded:

```bash
logfire-docs search live evals monitoring
logfire-docs grep 'push_dataset' --context 3
logfire-docs grep 'class \w+\(Evaluator' --slug '^evals/'
logfire-docs grep 'LLMJudge'
```

That last one is deliberately unfiltered. `--group Evaluations` would restrict it to the platform
section — where `LLMJudge` appears only in passing prose — and hide `evals/evaluators/llm-judge`,
which is the page that actually documents the class. Section names are close enough to mislead
("Evaluations" is the platform, "Pydantic Evals > Evaluators" is the library), so when you're
chasing a symbol rather than a screen, filter by `--slug` or not at all.

**Then read the section, not the page.** `--outline` gives you a page's headings for a few hundred
tokens, and `--section` pulls only what you name — worth doing by reflex, since spending a whole
page of context to answer one question is the most common way this skill gets expensive:

```bash
logfire-docs read evaluate/overview --outline
logfire-docs read evaluate/live-evals --section 'investigate|hide'
logfire-docs read evals/evaluators/llm-judge --section 'rubric|context'
```

**Leaf names repeat, so `read` may ask you to disambiguate.** `overview` alone names three pages —
under `evaluate/`, `deploy/self-hosted-deployment/` and `evals/evaluators/`. When `read` reports
multiple matches it prints the candidates with their sections, which is exactly the information
that tells the platform page from the library one; pick the slug rather than guessing.

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

You shouldn't need to — the cache holds every Logfire page and every `evals/*` page — but if you do
fetch one directly, use the `index.md` form exactly as it appears in `llms.txt`:
`https://pydantic.dev/docs/logfire/evaluate/overview/index.md` or
`https://pydantic.dev/docs/ai/evals/evaluators/custom/index.md`.

The docs ask agents to pass `goal` and `organization` query parameters so maintainers can see where
agents get stuck; the script exposes them as `--goal` and `--organization`. These go to an external
service, so keep them to a short public task description and a public company name — never anything
private or confidential. Omitting them is fine.

## Where the coverage stops

Evaluation is covered end to end here — platform and library both — so an eval question that comes
up empty is usually phrased wrong rather than out of scope. Retry with `grep` before concluding
the docs are silent.

What genuinely lives elsewhere:

- **The rest of Pydantic AI** — `Agent`, output types, tools and toolsets, dependencies, message
  history, streaming, model providers, MCP, durable execution — is the **`pydantic-ai-docs`
  skill's** corpus. Only the `evals/*` subtree of that site is mirrored here, so "how do I define
  an agent's output type" is a question for that skill even though it shares a doc site with
  pydantic-evals.
- **Core Pydantic validation** (`BaseModel`, validators, `Field`) is a third site again, and
  Claude Code questions belong to `claude-code-docs`.

The overlap with `pydantic-ai-docs` on `evals/*` is deliberate: both skills can answer a
pydantic-evals question, and either is fine. Reach for this one when the question also touches
tracing, experiments, or the Logfire UI — which eval questions usually do. `cookbook/evaluate-an-agent`
walks the instrument-then-evaluate path end to end and is a good place to start when the user's
situation spans both.
