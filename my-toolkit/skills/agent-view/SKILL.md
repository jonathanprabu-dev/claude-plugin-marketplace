---
name: agent-view
description: How to dispatch, monitor, and clean up Claude Code background sessions — the ones listed by `claude agents` (agent view). Use this whenever the user wants work to run in the background or in parallel, mentions `claude agents`, `--bg`, `/bg`, `/background`, `/fork`, attaching or detaching, a session that "needs input", the background supervisor or daemon, or a session that is stuck, stopped, unresponsive, or failed after a restart. Also use when background work edited files somewhere unexpected, opened a pull request on its own, left worktrees behind in `.claude/worktrees/`, or when deciding between a background session and a subagent for a task.
---

# Background sessions and agent view

A **background session** is a full Claude Code conversation that keeps running with no
terminal attached. `claude agents` — "agent view" — is the fullscreen table listing all of
them: what each is doing, which need input, which are done. Sessions survive closing the
terminal because a per-user **supervisor** process hosts them, not your shell.

This is a research preview. Behavior shifts release to release, so check
`claude --version` against the version-gate table in `references/troubleshooting.md`
before promising a specific behavior.

**Not the same thing as a subagent.** A subagent runs inside the current conversation and
reports back to it. A background session is its own conversation with its own quota, its
own worktree, and its own row you attach to. Reach for a background session when the work
is long, independent, and the user wants to walk away — not when you just need a search
fanned out.

## The most important thing: who runs which command

Two surfaces, and confusing them is the main way this goes wrong.

| Surface | Who runs it | Notes |
| :--- | :--- | :--- |
| `claude agents`, `claude attach <id>` | **The user types this in their terminal** | Both take over the terminal fullscreen. You cannot drive them. |
| `claude --bg`, `claude logs/stop/rm/respawn`, `claude agents --json`, `claude daemon ...` | You can run this via Bash | Non-interactive, scriptable. |

`claude attach` is the trap: it looks like an ordinary CLI command, but it replaces the
terminal with an interactive session and blocks. Never run it yourself — tell the user the
exact line to type. In this session they can prefix it with `!` to run it inline.

Slash commands inside a session — `/bg`, `/background`, `/fork`, `/stop`, `/rename` — are
likewise the user's to type.

What you can do without any of that: read state off disk (see
[Inspecting state](#inspecting-state-without-running-anything)) and dispatch or inspect
sessions with the non-interactive commands:

```bash
claude --bg "investigate the flaky SettingsChangeDetector test"
claude --bg --name flaky-test-fix --agent code-reviewer "address review comments on PR 1234"
claude --bg --exec 'pytest -x'          # a shell job, not a Claude session — no model runs
claude agents --json --all --cwd .      # structured list; --all includes completed
claude logs <id>                        # recent output
claude stop <id>  |  claude respawn <id> [--all]  |  claude rm <id>
```

`--bg` takes the prompt as a **positional** argument. Combining it with `-p`/`--print` is
rejected outright, because `--print` never starts the session agent view would attach to.

A shell job started with `--exec` keeps its output in memory only, and both the row and the
output are cleaned up about five minutes after the command exits. Read it before then.

## Moving an existing conversation into the background

Two commands, and the difference is the whole point:

- **`/background`** (alias `/bg`) **moves** the current conversation to a background session
  and frees the terminal. `←` on an empty prompt does the same in one keystroke. In-flight
  background shell commands, subagents, workflows, and `/loop` tasks carry over; a running
  monitor cannot and is stopped, which is what the `Background this session?` dialog is
  warning about. `CLAUDE_DISABLE_ADOPT=1` stops the carry-over instead.
- **`/fork`** **copies** it. The original keeps running, the copy becomes its own row, and
  from that moment the two are fully independent — nothing the copy does reaches the original.

The fork inherits the working directory, model, permission mode, effort, and any `/add-dir`
or "don't ask again" grants made during the session. With a prompt (`/fork open a draft PR
with the work so far`) it starts immediately; without one it waits for its first instruction.
If the current session is inside a linked worktree that has a main working tree, the copy runs
in that main tree so the two never share a checkout.

`/fork` needs 2.1.212+. On 2.1.161–2.1.211 it started a forked *subagent* instead — that
behavior is now `/subtask`, and it's also what `/fork` still does when agent view is turned
off. Sessions launched with a replaced system prompt or a `--tools` allowlist can't be forked
at all; Claude Code says so rather than making a partial copy.

Launch flags carry through either way: `--mcp-config`, `--strict-mcp-config`, `--settings`,
`--add-dir`, `--plugin-dir`, `--fallback-model`, `--allow-dangerously-skip-permissions`.

## Dispatch-input syntax

What the user types into the agent view input isn't just a prompt:

| Input | Effect |
| :--- | :--- |
| `<agent-name> ...` or `@<agent-name>` | Runs that custom subagent as the session's main agent. The bare first-word match fires too, so a prompt starting with a subagent's name dispatches it |
| `@<repo>` | Runs the session in a sibling git repo, a registered worktree inside the launch repo, or any directory already in the list. Directories with spaces in the name aren't offered |
| `!<command>` | Runs a shell job instead of a Claude session — no model, output in memory only |
| `/<command>` | Skills, custom commands, and prompt-expanding built-ins like `/init` dispatch as the first prompt |
| `#<number>` or a PR URL | Selects the session already working on that PR instead of dispatching |
| `a:<name>`, `s:<state>` | Filters the list (`s:blocked` covers everything waiting on you) |
| `Shift+Enter` | Dispatch and attach immediately |

A subagent name beats a sibling repo of the same name. A few commands run **in** agent view
rather than dispatching: `/model` (sets the dispatch model for the run), `/login`, `/logout`,
`/exit`, `/quit`, and a bare `/resume` (opens a picker of the repo's past sessions, including
deleted rows, and brings one back as a background session). Other built-ins show
`attach to a session to run it` and leave the typed text in the input.

## What the user sees, so you can describe it accurately

Rows group under **Pinned**, **Ready for review** (has an open PR), **Needs input**,
**Working**, and **Completed** (which collects finished, failed, *and* stopped). `Ctrl+S`
switches to grouping by directory instead. Key keys: `Space` peeks and
lets them reply without attaching, `Enter`/`→` attaches, `←` on an empty prompt detaches,
`Ctrl+T` pins, `Ctrl+R` renames, `Ctrl+X` stops and `Ctrl+X` again within two seconds
deletes, `?` lists everything.

The icon carries two independent facts: **color** is the session state, **shape** is whether
the process is alive. `∙` means the process exited — the session is still fine, and peeking
or replying starts a fresh one from where it left off. Don't read `∙` as broken.

A `#1234` at the right edge is a linked pull request, colored by status (yellow waiting,
green passing, purple merged, grey draft/closed). For most dispatched work that column is
where the result is picked up.

The one-line row summaries are written by a **Haiku-class model** — one short billed request
per turn end, plus a rewrite every few minutes during long turns. Worth mentioning only when
someone is auditing where their usage goes.

## Background sessions edit files in their own worktree

This is the biggest surprise, and the one to raise before dispatching anything.

A background session starts in your working directory but **moves into a git worktree under
`.claude/worktrees/` before its first edit**, so parallel sessions read the same checkout and
each writes to its own. It skips the move when it's already inside a linked worktree, when
the directory isn't a git repo and no `WorktreeCreate` hook is configured, or when the write
lands outside the working directory.

A session that isolated itself that way then **commits, pushes its own branch, and opens a
draft pull request without stopping to ask.** It never pushes to `main`/`master`, never
force-pushes, never merges. A session editing a checkout it did *not* isolate itself — because
isolation was off, the move failed, or it started inside an existing worktree — still asks
before committing or switching branches.

To turn isolation off for a repo where worktrees are impractical, in `.claude/settings.json`:

```json
{ "worktree": { "bgIsolation": "none" } }
```

Outside a git repository there is no isolation at all, so don't dispatch parallel sessions
onto the same files there.

**Deleting is where work gets lost.** `Ctrl+X` twice in agent view removes the worktree
*including uncommitted changes*. `claude rm` from the shell keeps a worktree that has
uncommitted changes, along with its row. Neither removes a worktree holding commits that
aren't pushed anywhere — that one is kept together with its session, and the reason is
printed. Say this once, plainly, before anyone deletes a row that edited files.

Subagents a background session spawns inherit its working directory, so their edits land in
that session's worktree, not the user's checkout.

## Inspecting state without running anything

Everything is on disk. Prefer reading it over asking the user to run commands.

| Path | What it tells you |
| :--- | :--- |
| `~/.claude/jobs/<id>/state.json` | Per-session state shown in agent view. The directory name **is** the short id |
| `~/.claude/jobs/<id>/tmp/` | Per-session scratch dir; writes there don't prompt. Also exported as `$CLAUDE_JOB_DIR/tmp` inside the session |
| `~/.claude/daemon/roster.json` | Running background sessions, used to reconnect after a supervisor restart |
| `~/.claude/daemon.log` | Supervisor log |

`claude daemon status` summarizes the same thing — reachability, pid, version, socket dir,
worker count — and warns when the running supervisor is on a different version than the
`claude` you invoked.

If `CLAUDE_CONFIG_DIR` is set, all of this moves there and that supervisor is a **separate
instance with its own sessions**. A user who "lost" their sessions after changing that
variable hasn't lost anything.

`claude agents --json` is the structured view: `cwd`, `kind`, `startedAt` always; `id` and
`state` (`working`/`blocked`/`done`/`failed`/`stopped`) for background sessions; `pid` and
`status` while alive; `waitingFor` when blocked; `sessionId` (usable with `claude --resume`)
and `name` when set. Without `--all` it lists active sessions only.

## Why a session isn't behaving the way the user expects

Check these before diagnosing anything deeper:

- **It went quiet / is slow to open.** After a session finishes and sits unattached ~1 hour,
  the supervisor stops its process to free resources. Attaching, peeking, or replying starts
  a fresh one from where it left off. `Ctrl+T` pins a session and exempts it.
- **It's on the wrong model or permission mode.** Backgrounding an existing session with
  `/bg` or `←` **keeps** its current mode; dispatching from the agent view input or
  `claude --bg` uses that directory's `defaultMode` (or the dispatched subagent's
  frontmatter). These are not the same path.
- **`bypassPermissions` is refused.** It requires having accepted the disclaimer once
  interactively via `claude --dangerously-skip-permissions`. This is deliberate for sessions
  nobody is watching.
- **It can't reach the LLM gateway.** A background session does **not** inherit
  `ANTHROPIC_BASE_URL` and friends from the shell that started the supervisor. Put the
  endpoint in the project's `.claude/settings.json` `env` block — that is the reliable fix.
  Shell-exported gateways only reach a session when the supervisor was started from that same
  gateway environment *and* the dispatch targets the directory you're dispatching from.
- **It restarted and lost its place.** The supervisor restarts crashed processes and tells the
  restarted session it was restarted, so it re-verifies time-sensitive context like branch
  state. Background shell commands, dynamic workflows, and background subagents hand off to
  the new process; running monitors do not, since their event stream can't move.
- **The whole feature is missing.** `disableAgentView: true` or
  `CLAUDE_CODE_DISABLE_AGENT_VIEW` turns it off, and administrators can enforce that via
  managed settings. If `claude agents` prints a list of subagents and exits, the version is
  too old — `claude update`.

## Cost

Each background session consumes subscription quota **independently**. Ten running in
parallel burn quota roughly ten times as fast as one. Row summaries add small Haiku-class
requests on top. Sessions are local: preserved across sleep, stopped by a shutdown.

Say this once when someone is about to fan out a dozen sessions, then respect the decision.

## Reference files

- `references/troubleshooting.md` — symptom-to-fix table for stuck, unresponsive, and failed
  sessions, auth and daemon failures, leftover worktrees, and the version-gate table for
  "it works on my machine". Read this whenever something isn't working.
