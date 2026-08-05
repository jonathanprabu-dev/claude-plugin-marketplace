# Troubleshooting plugins and marketplaces

## Contents

- [Symptom to fix](#symptom-to-fix)
- [Code intelligence / LSP problems](#code-intelligence--lsp-problems)
- [Diagnostic order](#diagnostic-order)
- [Version-gated behaviors](#version-gated-behaviors)

## Symptom to fix

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `/plugin` is an unknown command | Claude Code predates the plugin system, or you're not in the terminal CLI | `claude --version`, then upgrade: `brew upgrade claude-code`, `npm install -g @anthropic-ai/claude-code@latest`, or re-run the native installer. Restart the terminal. In the desktop app use the plugin browser; in cloud sessions declare `enabledPlugins` in `.claude/settings.json` |
| `Marketplace "claude-plugins-official" not found` | Startup auto-add was blocked, usually by the network | `/plugin marketplace add anthropics/claude-plugins-official` |
| Plugin not found in a marketplace that should have it | Local catalog copy is stale | `/plugin marketplace update <marketplace>`, then retry the install |
| Marketplace won't load | URL unreachable, or no `.claude-plugin/marketplace.json` at that path | Verify the path/URL and that the file exists at the expected location |
| Install fails | Source URL unreachable or repo is private | Confirm the repo is public or that you have access |
| Plugin skills don't appear at all | Corrupt plugin cache | Clear the cache, restart, reinstall (see below) |
| Skills missing but the plugin looks installed | The session hasn't reloaded | `/reload-plugins` |
| Edits to a local plugin have no effect | The loaded copy lives in the cache, not your source directory | `/plugin marketplace update <mkt>` + `/reload-plugins`; if `version` changed, uninstall and reinstall |
| Files referenced by a plugin are missing after install | The path pointed outside the plugin directory, which isn't copied into the cache | Move the file inside the plugin and reference it via `${CLAUDE_PLUGIN_ROOT}` |
| `/plugin disable` says "already disabled" but it stays on | Marketplace-entry name differs from `plugin.json` name, on a version before v2.1.195 | Upgrade, or use the other name |
| `path not found` installing from a URL-based marketplace | Relative plugin paths don't resolve from a hosted `marketplace.json` | Use a Git-based marketplace instead |
| Plugin can't be disabled or uninstalled at all | It's **managed** scope, pushed by an administrator | Nothing to do locally; it's an admin change |

### Clearing the plugin cache

macOS / Linux:

```bash
rm -rf ~/.claude/plugins/cache
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\plugins\cache"
```

Then restart Claude Code and reinstall the plugin. This is destructive to every installed
plugin's files — they get re-fetched — so treat it as a last resort, and confirm with the
user before running it.

## Code intelligence / LSP problems

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `Executable not found in $PATH` in the `/plugin` **Errors** tab | The plugin configures the language server but never installs the binary | Install the binary yourself — see the table in `official-catalog.md` |
| Language server won't start | Binary missing from `$PATH` | Verify with `(Get-Command <binary>).Source` on Windows or `which <binary>` elsewhere; check the Errors tab for detail |
| Memory spikes on a large project | `rust-analyzer` and `pyright` in particular are heavy | `/plugin disable <plugin-name>` and fall back to Claude's built-in search |
| Unresolved-import errors for internal packages in a monorepo | The language server's workspace isn't configured for the repo layout | Cosmetic — these false positives don't block editing. Fix the workspace config if it's noisy |

To read diagnostics yourself, press **Ctrl+O** when Claude Code shows something like
"Found 3 new diagnostic issues in 2 files".

## Diagnostic order

When a plugin, skill, or agent isn't behaving, check in this order — each step is cheap and
rules out the layer below it:

1. **Is it enabled?** Read `enabledPlugins` in `~/.claude/settings.json` (and the repo's
   `.claude/settings.json` / `.claude/settings.local.json` for project and local scope).
2. **Is it actually installed?** Read `~/.claude/plugins/installed_plugins.json`. Project
   settings can enable a plugin that was never installed — the enable flag alone does nothing.
3. **Where is it loading from?** The `installPath` field. Compare it to where the user has
   been editing. A mismatch is the single most common cause of "my changes did nothing".
4. **Did the session reload?** Install, enable, and disable all need `/reload-plugins`.
5. **Are there load errors?** `/plugin` → **Errors** tab.
6. **Is the cache corrupt?** Only then consider clearing it.

## Version-gated behaviors

Useful when a user's experience doesn't match the docs. Have them run `claude --version`.

| Version | What changed |
| :--- | :--- |
| 2.1.143 | Plugin details show a **Context cost** token estimate |
| 2.1.144 | Plugin details show **Last updated** |
| 2.1.145 | Plugin details show a **Will install** inventory of components |
| 2.1.154 | Plugins relevant to the working directory pin to the top of **Discover**, when an admin allowlists via `pluginSuggestionMarketplaces` |
| 2.1.163 | `/reload-plugins` warns and refuses when a plugin's MCP tools would invalidate the prompt cache; `--force` overrides |
| 2.1.187 | **Not used recently** group and the **Last used** line appear |
| 2.1.195 | Enable/disable works when the marketplace name and `plugin.json` name differ; project-enabled external plugins are install-gated on every load path |
| 2.1.196 | A git host typed without `https://` is rejected as an invalid GitHub shorthand instead of failing later at clone time |
| 2.1.203 | Uninstalling a project-enabled plugin offers "disable for me" **or** "uninstall for everyone"; LSP activity counts as plugin use |
| 2.1.206 | The first session on an LSP-usage-tracking version resets untracked LSP plugins, so an actively used one isn't mislabeled unused |

Note: the **Not used recently** header and **Last used** line are hidden entirely when an
organization sets `strictKnownMarketplaces`, so their absence isn't necessarily a version issue.
