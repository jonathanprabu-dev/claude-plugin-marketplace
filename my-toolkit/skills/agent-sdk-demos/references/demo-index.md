# Demo index

Clone root: `C:\dev\claude-agent-sdk-demos` (upstream: `anthropics/claude-agent-sdk-demos`, MIT).
All demos need `ANTHROPIC_API_KEY`; each has its own `.env.example` and README.

---

## hello-world — TypeScript

Single file: `hello-world/hello-world.ts`. The smallest complete `query()` usage.

Shows:
- `query({ prompt, options })` and iterating the returned generator, filtering for
  `message.type === 'assistant'` and pulling the `text` content block.
- A full `options` block: `maxTurns`, `cwd`, `model: "opus"`, `executable: "node"`,
  an explicit `allowedTools` allowlist.
- A `PreToolUse` hook with `matcher: "Write|Edit|MultiEdit"` returning
  `HookJSONOutput` — `{ continue: true }` to allow, or
  `{ decision: 'block', stopReason, continue: false }` to reject a write outside a
  sandbox directory. This is the canonical hook-signature reference.

Setup gotcha: `cwd` points at an `agent/` subdirectory that **is not in the repo**.
Run `mkdir -p agent/custom_scripts` inside `hello-world/` first or the SDK fails with
`Failed to spawn Claude Code process: ... ENOENT`. The separation is deliberate — the
agent's working root is not the host process's — but you have to create it.

`hello-world/README.md` is the best prose explanation of the SDK in the repo: it covers
the three message types (`system`, `assistant`, `result`), the full `options` list, the
subprocess architecture (the SDK spawns a Claude Code CLI process and talks over
stdin/stdout), and a troubleshooting section. Read it alongside the code.

---

## hello-world-v2 — TypeScript

Single file: `hello-world-v2/v2-examples.ts`. The V2 Session API (`unstable_v2_*`).

Four labelled examples:
- `basicSession()` — `await using session = unstable_v2_createSession({ model: 'sonnet' })`,
  then `await session.send(...)` and `for await (const msg of session.stream())`.
  The `await using` matters: it disposes the session.
- `multiTurn()` — two `send()`/`stream()` rounds where the second depends on the
  first's answer. This is V2's main advantage over re-invoking `query()`.
- `oneShot()` — `unstable_v2_prompt(prompt, opts)` returns a result directly.
- `sessionResume()` — capture the session id from the stream, then
  `unstable_v2_resumeSession(sessionId, opts)` in a later block and confirm the
  context survived.

Imports to copy: `unstable_v2_createSession`, `unstable_v2_resumeSession`,
`unstable_v2_prompt`.

---

## research-agent — Python

`research-agent/research_agent/agent.py` plus `prompts/` and `utils/`.
Multi-agent orchestration: a lead agent decomposes a request, spawns parallel
researchers, and a report writer synthesizes.

Shows:
- `ClaudeSDKClient` used as `async with ClaudeSDKClient(options=options) as client`.
- `ClaudeAgentOptions` with `agents={...}` mapping names to `AgentDefinition`
  (`researcher`, `data-analyst`, `report-writer`), and `allowed_tools=["Task"]` —
  the lead agent can *only* delegate.
- `setting_sources=["project"]` to load the project's `.claude/` directory, which is
  how the bundled skills and slash commands become available to the SDK agent.
- `hooks={...}` built from `HookMatcher`, wired to `PreToolUse`/`PostToolUse`
  handlers on a `SubagentTracker` for live activity tracking.
- System prompts kept as plain `.txt` files in `prompts/`, not inline strings.

Bundled under `research-agent/.claude/`:
- `commands/` — `research`, `fact-check`, `competitive-analysis`, `market-trends`, `summarize`
- `skills/executive-briefing/`, `skills/pdf/` (with Python form-filling scripts)

Good template for any "orchestrator + workers" SDK app in Python.

---

## ask-user-question-previews — TypeScript

`ask-user-question-previews/server.ts` + `client/`. A branding assistant that renders
AskUserQuestion options as styled HTML cards in a browser.

Shows:
- `toolConfig: { askUserQuestion: { previewFormat: "html" } }` — opts each option into
  carrying an HTML mockup instead of a bare label.
- `canUseTool: async (toolName, input) => {...}` as an async gate: it blocks, pushes the
  question to the browser over WebSocket, and resolves when the user answers. The
  pending-question map is the pattern worth copying for any human-in-the-loop UI.
- Rejecting non-AskUserQuestion tools by returning a message steering Claude back to
  asking. The comments note that some tools still fire even when `tools` lists only one.
- `permissionMode: "plan"` to keep Claude clarifying before acting.
- Distinguishing `text` vs `tool_use` content blocks when forwarding to the client.

The clearest reference for `canUseTool` and for streaming tool calls to a frontend.

---

## simple-chatapp — TypeScript (React + Express)

`simple-chatapp/server/` — `ai-client.ts`, `session.ts`, `chat-store.ts`, `server.ts`,
`types.ts` — plus `client/`. Full conversation loop with streaming over WebSocket.

`ai-client.ts` holds the key pattern for a long-lived, two-way session: an
`AgentSession` class whose constructor passes a `MessageQueue` **as the prompt**
(`prompt: this.queue as any`) rather than a string, then grabs
`[Symbol.asyncIterator]()` off the `query()` return and stores it on the instance.
`sendMessage()` just pushes onto the queue; `getOutputStream()` pumps the stored
iterator. That's how you keep one SDK session open across many user turns instead of
starting a new `query()` per message. Read `ask-user-question-previews` for permission
handling. Has `CLAUDE.md`, `diagram.png`,
and `demo.gif` explaining the architecture.

---

## email-agent — TypeScript (largest demo)

IMAP assistant: inbox display, agentic search, AI assistance. In development upstream.

`email-agent/ccsdk/` is the SDK integration layer and the most substantial reference here:
`ai-client.ts`, `session.ts`, `custom-tools.ts`, `message-queue.ts`, `websocket-handler.ts`,
`ui-state-manager.ts`, `component-manager.ts`, `actions-manager.ts`, `listeners-manager.ts`,
`log-writer.ts`, `email-agent-prompt.ts`, `types.ts`.

`email-agent/agent/` is the agent's own workspace: `.claude/agents/inbox-searcher.md`,
`.claude/skills/action-creator/` and `.claude/skills/listener-creator/` (each with
TypeScript templates), and `custom_scripts/` holding code the agent generates at runtime.

Design docs worth reading before borrowing from it: `ACTIONS_SPEC.md`,
`LISTENERS_SPEC.md`, `UI_STATE_SYSTEM.md`, `UI_STATE_COMPONENTS_SPEC.md`,
`recursive-code-generation.md` (the agent writing and executing its own scripts),
plus `CLAUDE.md` and `architecture.png`.

---

## excel-demo — TypeScript (Electron)

Electron-React-Boilerplate desktop app wrapping an agent that manipulates spreadsheets.
`excel-demo/src/` is the app; `excel-demo/agent/` is the agent workspace, containing
`.claude/skills/xlsx/` (with `recalc.py`), `CLAUDE.MD`, and `requirements.txt` — the
agent shells out to Python for spreadsheet work.

Reference for packaging an SDK agent into a desktop app and for pairing a TS agent with
a Python toolchain.

---

## resume-generator — TypeScript

`resume-generator/resume-generator.ts`. Web-searches a person's name and assembles a
one-page `.docx`. Bundles `.claude/skills/docx/` (`SKILL.md` + `docx-js.md`).

Smallest example of "agent + a document skill + web search" producing a real file.
