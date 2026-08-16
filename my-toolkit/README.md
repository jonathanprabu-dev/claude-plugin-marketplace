# my-toolkit

A Claude Code plugin bundling my personal skills and agents.

## What's inside

**Skills** (`skills/`)
- `agent-sdk-demos` — index of Anthropic's official Claude Agent SDK demo apps, cloned
  at `C:\dev\claude-agent-sdk-demos`, mapped by what you're building.
- `agent-view` — dispatch, monitor, and clean up background sessions (`claude agents`).
- `claude-code-docs` — search and quote the official Claude Code docs instead of memory.
- `logfire-docs` — search and quote the official Pydantic Logfire docs instead of memory.
- `plugin-marketplaces` — discover, install, and manage plugins and marketplaces.
- `pydantic-ai-docs` — search and quote the official Pydantic AI docs instead of memory.
- `skill-creator` — create, improve, and eval-test Claude Code skills.

**Agents** (`agents/`)
- `code-reviewer` — reviews a code diff for correctness bugs and cleanups.
- `test-runner` — detects and runs a project's test suite, reports pass/fail.
- `verification-qa` — verifies a change end-to-end by driving the affected flow.
- `embedding-contract-guard` — guards embedding invariants in Gemini-embedding RAG codebases.

## Install

From this repo's parent folder, add it as a local marketplace and install:

```
/plugin marketplace add "C:\dev\DIscover & install pre built plugins & Create plugins"
/plugin install my-toolkit@my-marketplace
```

Or for quick testing without installing, launch Claude Code with:

```
claude --plugin-dir "C:\dev\DIscover & install pre built plugins & Create plugins\my-toolkit"
```

## Structure

```
my-toolkit/
├── .claude-plugin/
│   └── plugin.json      # plugin manifest (name, version, author)
├── agents/              # subagent definitions (*.md with frontmatter)
├── bin/                 # launchers Claude Code puts on PATH (claude-code-docs, logfire-docs, pydantic-ai-docs)
└── skills/              # one directory per skill: SKILL.md + references/scripts
```
