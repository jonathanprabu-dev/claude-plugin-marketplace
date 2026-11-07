# my-toolkit

A Claude Code plugin bundling my personal skills and agents.

## What's inside

**Skills** (`skills/`)
- `agent-sdk-demos` — index of Anthropic's official Claude Agent SDK demo apps, mapped
  by what you're building.
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

Add this repo as a marketplace in Claude Code, then install the plugin:

```
/plugin marketplace add jonathanprabu-dev/claude-plugin-marketplace
/plugin install my-toolkit@my-marketplace
```

Or, from a local clone, test it without installing:

```
claude --plugin-dir ./my-toolkit
```

`agent-sdk-demos` expects a local clone of
[anthropics/claude-agent-sdk-demos](https://github.com/anthropics/claude-agent-sdk-demos);
edit the path in its SKILL.md to match yours.

## Credits

`skill-creator` is Anthropic's open-source skill-creator skill (Apache 2.0, see its
`LICENSE.txt`), bundled here with its licence.

## Structure

```
my-toolkit/
├── .claude-plugin/
│   └── plugin.json      # plugin manifest (name, version, author)
├── agents/              # subagent definitions (*.md with frontmatter)
├── bin/                 # launchers Claude Code puts on PATH (claude-code-docs, logfire-docs, pydantic-ai-docs)
└── skills/              # one directory per skill: SKILL.md + references/scripts
```
