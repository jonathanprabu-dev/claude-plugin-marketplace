---
name: claude-code-docs
description: Search and quote the official Claude Code documentation at code.claude.com/docs instead of answering from memory. Use this whenever a question touches Claude Code itself — hooks, skills, subagents, agent teams, agent view, plugins and marketplaces, MCP servers, settings.json, permissions, sandboxing, CLAUDE.md, slash commands, keybindings, worktrees, checkpointing, scheduled tasks, the CLI flags and env vars, IDE/desktop/web clients, enterprise setup (Bedrock/Vertex/Foundry, gateways, ZDR), the Agent SDK (Python and TypeScript), or "what's new" release notes. Trigger it for phrasings like "can Claude Code...", "how do I configure...", "what setting controls...", "why isn't my hook firing", "is that flag still supported", or any question naming a Claude Code setting, env var, hook event, or CLI flag — even when you think you already know the answer, because Claude Code ships weekly and behavior in your training data is often stale.
---

# Claude Code documentation search

Claude Code changes every week: flags get renamed, settings get added, features move
between research preview and general availability. Answering from memory is how you
end up confidently describing a flag that no longer exists. The docs are the source of
truth, they are small, and searching them takes about a second — so search first and
quote what you find.

Every page is published as raw markdown at its `.md` URL, and there is a machine-readable
index of all ~175 pages at `https://code.claude.com/docs/llms.txt`. The bundled script
wraps both.

## The script

`claude-code-docs` is a launcher in the plugin's `bin/`, which Claude Code puts on **the Bash
tool's** PATH — so it runs from any working directory and you never need to know where the
plugin lives. That PATH injection covers the Bash tool only. From the PowerShell tool the bare
command is not found; use the direct invocation below instead.

```bash
claude-code-docs search <terms...>     # rank pages by title/description — instant
claude-code-docs read <slug|url>       # print one page's full markdown
claude-code-docs grep <regex>          # full-text search across every page
claude-code-docs index                 # list all pages, for browsing
```

If the shell reports the command isn't found — you're in the PowerShell tool, or the plugin was
installed after this session started — call the script directly. The script locates its own cache
relative to itself, so any absolute path works.

**Always quote the path.** Plugin roots routinely contain spaces, and a marketplace installed from
a directory can contain `&`, `(`, or `'` too — all of which break an unquoted command in both
shells. Quote it even when the current path looks harmless:

```bash
python "<plugin-root>/skills/claude-code-docs/scripts/docs.py" search <terms...>
```

```powershell
& python "<plugin-root>\skills\claude-code-docs\scripts\docs.py" search <terms...>
```

`<plugin-root>` is available to hooks as `${CLAUDE_PLUGIN_ROOT}`, but that variable is *not* set in
the Bash or PowerShell tool environment — substitute the literal path there. The `bin/claude-code-docs.cmd`
shim works the same way from PowerShell, again quoted and behind the `&` call operator.

Useful flags: `--slug <regex>` narrows `grep` to matching pages, `--context N` widens
grep context lines, `--limit N` caps results, `--json` for structured output, and
`--refresh` bypasses the cache when you suspect the docs just changed.

Pages are cached under `~/.cache/claude-code-docs` for 24 hours. The first `grep` pulls
the whole corpus (~7 MB, roughly 20 seconds); every call after that is instant.

## How to answer a question

**Start with `search`.** The index carries a one-line description per page, so conceptual
questions usually land on the right page immediately:

```bash
claude-code-docs search hooks permission bash
```

**Use `grep` when the question names a specific string** — an env var, a setting key, a
flag, an error message. Titles won't contain `CLAUDE_CODE_DISABLE_BG_EXIT_HANDOFF`, but
the body will:

```bash
claude-code-docs grep 'leftArrowOpensAgents' --context 3
claude-code-docs grep 'permission-mode' --slug 'cli-reference|permissions'
```

**Then `read` the page** you landed on, to get the surrounding explanation rather than an
isolated line. Some pages are long (`agent-view`, `hooks`, `settings`, `agent-sdk/python`
run past 700 lines). When you only need one section of a large page, `grep --slug <page>`
with a wide `--context` pulls the region without spending context on the rest.

**Cross-check when the answer sounds surprising.** If one page says a flag exists and you
remember otherwise, grep for the flag across everything — the reference page and the guide
page sometimes describe different versions of the same feature, and the version history
tables at the bottom of pages resolve which is current.

## Reporting what you found

Quote the docs rather than paraphrasing from memory, and cite the human-readable URL:
`https://code.claude.com/docs/en/hooks` — that's the `.md` URL with the extension dropped,
which the script already prints for you.

Two things worth flagging to the user when they show up:

- **Version gates.** Pages mark recently-added behavior with `{/* min-version: 2.1.212 */}`
  comments and list changes in a version-history table. If the answer depends on one, say
  which version introduced it, and check what the user is running with `claude --version`.
- **Research preview / deprecation notes.** Features in preview change shape without warning,
  and the docs say so explicitly. Pass that caveat along rather than presenting the behavior
  as settled.

If the docs genuinely don't cover something, say so plainly instead of filling the gap with
a plausible-sounding guess. "The docs don't document this; here's the closest thing they do
cover" is a more useful answer than an invented setting name.

## Docs describe intent; the local install is the fact

The docs say what Claude Code is supposed to do. When the user's question is "why isn't
*my* config working", the docs give you the correct shape and local evidence gives you the
discrepancy: `/context` for what actually loaded, `/doctor` for configuration health,
`claude --version` against the page's version gates, and the settings files themselves.
A page and a live session disagreeing is usually a version gap, not a doc error.

## When the index itself fails

If `search` returns nothing and `grep` finds nothing, the topic may live outside these docs
— the Claude API, claude.ai, or a third-party plugin all have their own sources. Check
`index` to confirm the coverage boundary before reaching for a web search.

The boundary that gets crossed most often is "SDK" questions. Four different products
answer to that word, and only two of them are documented here. `agent-sdk/overview` carries
the comparison table that settles it — read it before answering, and route accordingly:

- **Agent SDK** (`agent-sdk/*`) — the Python/TypeScript library that runs the Claude Code
  agent loop in your own process. Documented here.
- **Claude Code CLI** (`overview`, `cli-reference`, `headless`) — the terminal interface.
  Documented here. For languages the SDK doesn't ship for, the answer is usually
  `headless`: run the CLI as a subprocess with `-p` and `--output-format json`.
- **Client SDK** — the raw Anthropic API SDK, where you implement the tool loop yourself.
  Lives at `platform.claude.com`, not here.
- **Managed Agents** — Anthropic-hosted agents and sandbox, a separate product from the
  Agent SDK. Also `platform.claude.com`.

So a question about `client.beta.messages.tool_runner`, prompt caching, or model IDs is a
Client SDK question and these docs will not have it, however much it sounds like an SDK
question. The `claude-api` skill and the `claude-code-guide` subagent cover that side.
