# my-toolkit

A Claude Code plugin bundling my personal skills and agents.

## What's inside

**Skills** (`skills/`)
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
└── skills/
    └── skill-creator/   # SKILL.md + scripts, references, assets
```
