# Agent view troubleshooting

Symptom first. Most of these are not bugs — they're the supervisor doing something
deliberate that looks like a failure.

## Symptom to fix

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `claude agents` prints a count and your subagents, then exits | Version too old, or agent view turned off | `claude update`; then check `disableAgentView` and `CLAUDE_CODE_DISABLE_AGENT_VIEW` |
| Agent view opens empty with just section headers | No sessions dispatched yet | Type a prompt in the input and press Enter |
| `Too short` when dispatching | Prompt under four characters | Guard against stray keystrokes; describe the task |
| Every session shows failed after a reboot | Shutdown stops running sessions | Attach, peek, or reply to any of them — each restarts from where it left off. Sleep alone does *not* cause this |
| Row says `possibly low memory — free some up and retry` | Process exited silently while the host reported low memory | A hypothesis, not a confirmed cause. Free memory, then peek or reply to restart it |
| "The background service did not respond" | Supervisor stalled | `claude daemon stop --any --keep-workers`, then reopen. `--keep-workers` is what preserves the running sessions |
| That stop command hangs on Windows | Supervisor not responding to the request | It prints a pid; finish with `taskkill /PID <pid>`. Sessions survive if `--keep-workers` was passed |
| `claude daemon status` reports a locked/unreadable pipe-key file (Windows) | File lock on the daemon key | Surfaced as the underlying file error, not a generic connection failure — treat it as a file problem |
| `Could not resolve authentication method` on dispatch only | The supervisor process itself had no stored credential to snapshot into the worker | Confirm `/login` or an API key, then `claude daemon stop --any --keep-workers`. If you authenticate by env var, run the next command from a shell where it is set |
| `This conversation is already open in another running Claude session` | Two processes can't write one transcript | Reply in the session that holds it, or exit it and reopen the row. A reply typed on the refused attempt is delivered on next start |
| `This session has no saved transcript` | Backgrounded from another conversation and stopped before its first response finished | The original conversation is intact — `claude --resume` it. To restart the row empty: press Enter again on it, or `claude respawn <id>` |
| Row shows only the original prompt after a restart | Transcript misread as empty | The old transcript is renamed with an `.orphaned-` suffix, not deleted — it's still on disk |
| Session slow to respond right after attaching | Idle process was stopped ~1h after finishing | Expected. Pin with `Ctrl+T` to keep it warm |
| A session went unresponsive after the machine slept | Mid-response when it slept | Opening it restarts the process and continues the interrupted response |
| `Background this session?` dialog on `←` | In-flight work that can't move, e.g. a running monitor | `/tasks` to see what's running; confirm to stop it, or Stay and let it finish |
| Backgrounding restarts subagents instead of carrying them | `←` pressed a second time while waiting | The ten-second wait doesn't apply to subagents; one press waits so their work carries over |
| `.claude/worktrees/` filling up | Deletes that couldn't safely remove a worktree, or ones git no longer tracks | `git worktree list`, then `git worktree remove <path>`. A directory git no longer recognizes is left on disk and must go by hand |
| A delete "didn't work" | Refused deliberately | The row shows `not deleted` with the reason — unpushed commits, another session's claim, or the raw git error |
| An empty row vanished on its own | A row created by `←` that never got a prompt | Removed after ~5 minutes. `claude --bg` sessions and ones awaiting a trust dialog are not |
| Ambiguous `←` right after attaching (Windows) | Terminal redelivering a pre-attach keypress | `Ambiguous ←, press again to detach` — press again |
| A `/plugin`-style command is refused in the session | Some commands need a terminal | `/install-github-app` and the `/mcp` settings list work while attached; unattached, the row shows `open this session to manage MCP servers`. `/mcp reconnect|enable|disable` work either way |
| Sessions "disappeared" after changing config | `CLAUDE_CONFIG_DIR` gives a separate supervisor instance with its own sessions | Restore the variable; nothing was deleted |

macOS-only, noted for completeness: background sessions request Full Disk Access and Local
Network permission separately from your terminal, so `~/Desktop` reads can fail with
`Operation not permitted` and LAN addresses with `connect: no route to host` until granted in
System Settings.

## Version gates

Agent view moves fast. When a behavior is disputed, check `claude --version` against this.

| Version | Change |
| :--- | :--- |
| 2.1.139 | Agent view introduced (research preview) |
| 2.1.141 | `--cwd` scoping |
| 2.1.142 | `--permission-mode`, `--model`, `--effort`, `--dangerously-skip-permissions`, `--settings`, `--add-dir`, `--plugin-dir`, `--mcp-config`, `--strict-mcp-config` |
| 2.1.143 | `worktree.bgIsolation`; `--allow-dangerously-skip-permissions` |
| 2.1.145 | Voice dictation in the peek-panel reply input and the dispatch input |
| 2.1.157 | `--agent` on `claude agents` |
| 2.1.161 | Row summaries show a `done/total` count for parallel work items |
| 2.1.172 | `/model` in the dispatch input sets a session-scoped override |
| 2.1.174 | Gateway vars no longer inherited from the supervisor's launch shell; fixes spurious auth errors |
| 2.1.191 | `claude --bg --agent <unknown>` fails the launch instead of falling back to the default agent |
| 2.1.195 | In-flight work carries over on Windows too (`CLAUDE_DISABLE_ADOPT=1` opts out) |
| 2.1.196 | A single `←` backgrounds a foreground session; `CLAUDE_CODE_DISABLE_BG_EXIT_HANDOFF=1` added |
| 2.1.198 | Notifications via `preferredNotifChannel` + `Notification` hook (`agent_needs_input`, `agent_completed`); isolated sessions open draft PRs without asking; `--bg` with `-p`/`--print` rejected; `←`/`/exit` in `claude attach` return to agent view |
| 2.1.199 | `possibly low memory` note; `/color` carries over when backgrounding |
| 2.1.200 | An unresponsive session is restarted on open and continues the interrupted response; `roster.json` preserves newer versions' fields; `--plugin-dir` after `agents` reaches agent view's own autocomplete |
| 2.1.202 | A `/rename` survives a supervisor-driven process restart |
| 2.1.203 | Dispatching shell's `PATH` applied to workers; `←` waits for subagents; `@` lists worktrees |
| 2.1.205 | `←` footer hint counts agents needing input; richer row summaries; `claude attach` waits ~60s for a restarting session |
| 2.1.206 | Row summaries fill the row width; deleting also clears the supervisor's session list; `CLAUDE_CODE_EXTRA_BODY` reaches background sessions |
| 2.1.207 | Peek panel opens with the sentence the row truncates and shows a single `waiting 3m` line; re-pasting expands a `[Pasted text #N]` placeholder; a session named by accepting a plan shows that name; a session that moved into a worktree keeps its conversation across a restart |
| 2.1.208 | Undeliverable replies are saved and sent on next start; transcript tail shown while a stopped session starts |
| 2.1.210 | `claude attach` waits while the service starts instead of erroring; `--effort ultracode` accepted |
| 2.1.211 | Gateway forwarded again when waking a stopped session; refused deletes show the reason on the row |
| 2.1.212 | `/fork` copies the conversation into a new background session (the old forked-subagent behavior moved to `/subtask`); bare `/resume` picker in agent view; sandbox/MCP/managed-settings waits report as `Needs input` |
| 2.1.213 | `/install-github-app` and `/mcp` work while a terminal is attached |
| 2.1.216 | Those commands surface a `Needs input` row instead of a flat refusal when unattached |
| 2.1.218 | `←` confirms with a second press after a delete or history move; Windows ambiguous-`←` notice |

For anything not listed, look it up rather than guessing — the `claude-code-docs` skill in
this plugin greps the live docs, and the `agent-view` page carries the authoritative version
history.
