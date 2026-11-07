# Claude Code plugin marketplace

My personal Claude Code plugin marketplace. It ships one plugin, **my-toolkit**: 7 skills and 4 subagents I use day to day when building AI agents and apps with Claude Code.

## Install

In Claude Code:

```
/plugin marketplace add jonathanprabu-dev/claude-plugin-marketplace
/plugin install my-toolkit@my-marketplace
```

## What's in my-toolkit

| Type | Name | What it does |
|---|---|---|
| Skill | claude-code-docs | Searches and quotes the official Claude Code docs instead of answering from memory |
| Skill | pydantic-ai-docs | Same for the Pydantic AI docs |
| Skill | logfire-docs | Same for the Pydantic Logfire docs |
| Skill | agent-sdk-demos | Index of Anthropic's Claude Agent SDK demo apps, mapped by what you're building |
| Skill | agent-view | Dispatches, monitors and cleans up background Claude sessions |
| Skill | plugin-marketplaces | Finds, installs and manages plugins and marketplaces |
| Skill | skill-creator | Creates, improves and eval-tests skills (Anthropic's open-source skill, Apache 2.0) |
| Agent | code-reviewer | Reviews a code diff for correctness bugs and cleanups |
| Agent | test-runner | Detects and runs a project's test suite and reports pass/fail |
| Agent | verification-qa | Verifies a change end to end by driving the affected flow |
| Agent | embedding-contract-guard | Guards embedding invariants in Gemini-embedding RAG codebases |

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest
my-toolkit/
├── .claude-plugin/plugin.json    # plugin manifest
├── agents/                       # subagent definitions
├── bin/                          # docs-search launchers added to PATH
└── skills/                       # one folder per skill: SKILL.md + references/scripts
```

More of my work: [github.com/jonathanprabu-dev](https://github.com/jonathanprabu-dev)
