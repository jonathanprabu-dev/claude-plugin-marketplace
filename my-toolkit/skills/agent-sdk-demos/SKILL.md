---
name: agent-sdk-demos
description: Working reference implementations for the Claude Agent SDK, from Anthropic's official claude-agent-sdk-demos repo, cloned locally. Use whenever building or debugging an app on top of `@anthropic-ai/claude-agent-sdk` (TypeScript) or `claude_agent_sdk` (Python) — headless agents, `query()` loops, the V2 session API, subagents via AgentDefinition, SDK hooks, custom in-process MCP tools, `canUseTool` permission callbacks, AskUserQuestion with HTML previews, streaming to a web UI over WebSocket, session persistence and resume, or loading project skills into an SDK agent with setting_sources. Read the matching demo before writing SDK code from memory — these are the patterns Anthropic actually ships, and the SDK surface changes faster than training data.
---

# Claude Agent SDK — official demo implementations

Anthropic's demo repo is cloned at **`C:\dev\claude-agent-sdk-demos`**. It is not a
plugin and has no skills of its own to install — its value is that every demo is
real, runnable SDK code. When a task involves the Agent SDK, **read the relevant
file from this clone instead of recalling the API** — a shipped implementation beats
a remembered signature.

Clone is pinned at commit `826b268` (2026-03-13). Check that date before trusting it
against current SDK docs; refresh with the command below if it looks stale.

> These are local-development demos, not production templates. Copy the *patterns*
> (option shapes, message-loop structure, hook signatures); do not copy the lack of
> auth, error handling, or input validation.

## Pick by what you're building

| You need | Read |
| :--- | :--- |
| The minimal `query()` loop, message iteration | `hello-world/hello-world.ts` |
| A `PreToolUse` hook that blocks a write | `hello-world/hello-world.ts` (same file, `options.hooks`) |
| V2 session API: `send()` / `stream()` instead of one generator | `hello-world-v2/v2-examples.ts` |
| Multi-turn conversation holding context | `hello-world-v2/v2-examples.ts` → `multiTurn()` |
| One-shot prompt with no session plumbing | `hello-world-v2/v2-examples.ts` → `oneShot()` |
| Persist a session and resume it later | `hello-world-v2/v2-examples.ts` → `sessionResume()` |
| Subagents / orchestrator-worker, parallel research | `research-agent/research_agent/agent.py` |
| Loading project `.claude/` skills + commands into an SDK agent | `research-agent/` (`setting_sources=["project"]`) |
| Tracking what subagents are doing, transcripts | `research-agent/research_agent/utils/` |
| Streaming to a React UI over WebSocket | `simple-chatapp/server/ai-client.ts`, `server/session.ts` |
| `canUseTool` permission callback round-tripped to a browser | `ask-user-question-previews/server.ts` |
| AskUserQuestion with rendered HTML option cards | `ask-user-question-previews/server.ts` (`toolConfig.askUserQuestion.previewFormat`) |
| Plan mode used to force clarifying questions first | `ask-user-question-previews/server.ts` (`permissionMode: "plan"`) |
| Custom in-process tools, session/queue/state managers | `email-agent/ccsdk/` |
| Agent that writes and runs its own code at runtime | `email-agent/` (`recursive-code-generation.md`) |
| Bundling an agent inside an Electron desktop app | `excel-demo/` |
| Shipping a document skill (docx/xlsx/pdf) with an agent | `resume-generator/.claude/skills/docx/`, `excel-demo/agent/.claude/skills/xlsx/` |

Full per-demo notes, including which language each uses and what it demonstrates:
[references/demo-index.md](references/demo-index.md).

## The two SDK surfaces

Both appear in this repo; don't mix them in one file.

- **V1** — `query({ prompt, options })` returns an async generator you `for await` over.
  Everything except `hello-world-v2` uses this. Options live in `options` (TS) or
  `ClaudeAgentOptions` (Python).
- **V2 (`unstable_v2_*`)** — `unstable_v2_createSession()`, then `await session.send(...)`
  and `for await (const msg of session.stream())`, with `unstable_v2_resumeSession(id)`
  and a `unstable_v2_prompt()` convenience. Uses `await using` for disposal. Still
  prefixed unstable — check current docs before depending on it.

Python names differ from TypeScript: `ClaudeSDKClient` / `ClaudeAgentOptions` /
`AgentDefinition` / `HookMatcher`, and options are `snake_case` (`allowed_tools`,
`setting_sources`) versus TS `camelCase` (`allowedTools`, `maxTurns`).

## Working with the clone

The clone is `--depth 1` on `main`. `git pull` on a shallow clone is unreliable once
upstream has moved, so refresh with fetch + reset instead:

```bash
git -C /c/dev/claude-agent-sdk-demos fetch --depth 1 origin main
git -C /c/dev/claude-agent-sdk-demos reset --hard origin/main
```

Run a demo from its own directory — each has its own `package.json` /
`pyproject.toml`, its own README, and its own `.env.example` needing
`ANTHROPIC_API_KEY`. Nothing is installed by default; `bun install` or
`uv sync` inside the demo folder first. Several demos also need directories
created by hand (see each README) — a missing `cwd` surfaces as
`Failed to spawn Claude Code process ... ENOENT`.

## Related

- `agent-sdk-dev` plugin: `/new-sdk-app` scaffolds a fresh SDK app, and the
  `agent-sdk-verifier-py` / `agent-sdk-verifier-ts` agents check a finished one.
  Use those to *build*; use this skill to see *how Anthropic did it*.
- `claude-api` skill for model IDs, pricing, and raw Messages API questions.
