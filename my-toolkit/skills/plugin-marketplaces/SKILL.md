---
name: plugin-marketplaces
description: How to discover, install, and manage Claude Code plugins and plugin marketplaces. Use this whenever the user mentions plugins or marketplaces in any form — installing or uninstalling a plugin, adding a marketplace, "what plugins do I have", enabling/disabling something, a plugin or skill that isn't showing up, a language server that won't start, plugin scopes, team/project plugin config, auto-updates, or developing a local plugin and wanting the changes to take effect. Also use when a skill or agent the user expects is missing, since that is usually a plugin loading problem rather than a code problem.
---

# Plugin and marketplace management

Plugins extend Claude Code with skills, agents, hooks, MCP servers, and LSP servers.
A **marketplace** is a catalog of plugins. Using one is always two steps: add the
catalog, then install individual plugins from it. Adding a marketplace installs
nothing on its own — think of it as adding an app store, not downloading apps.

## The most important thing: who runs which command

There are two command surfaces, and confusing them is the main way this goes wrong.

| Surface | Who runs it | Notes |
| :--- | :--- | :--- |
| `/plugin ...` | **The user types this in their terminal** | Interactive TUI. Several forms open a panel that stays open until Esc. You cannot drive it. |
| `claude plugin ...` | You can run this via Bash | Non-interactive, scriptable. Use for installs, listing, uninstalls in automation. |

So when the user needs a `/plugin` command, **tell them the exact line to type** rather
than trying to execute it. In this session they can prefix it with `!` to run it inline.
When you need to actually change something yourself, reach for `claude plugin` instead.

You can also answer most "what's installed / what's enabled" questions by reading files
directly — see [Inspecting state without running anything](#inspecting-state-without-running-anything).
That's usually faster and never risks opening a panel the user has to dismiss.

## Adding a marketplace

```
/plugin marketplace add <source>
```

`marketplace` shortens to `market`, and `remove` shortens to `rm`.

| Source form | Example | Notes |
| :--- | :--- | :--- |
| GitHub shorthand | `anthropics/claude-code` | `owner/repo`, must contain `.claude-plugin/marketplace.json` |
| Git URL | `https://gitlab.com/company/plugins.git` | Any host. Keep the `https://` **and** the `.git` |
| Git over SSH | `git@gitlab.com:company/plugins.git` | |
| Pinned ref | `https://gitlab.com/co/p.git#v1.0.0` | Append `#branch-or-tag` |
| Local directory | `./my-marketplace` or an absolute path | Quote paths containing spaces |
| Remote JSON | `https://example.com/marketplace.json` | Plugins using relative paths can fail from URL sources |

Two failure modes worth pre-empting: dropping `https://` makes recent versions reject the
string as a malformed GitHub shorthand, and dropping `.git` makes Claude Code treat the URL
as a direct link to a hosted `marketplace.json` instead of cloning.

**The official Anthropic marketplace** (`claude-plugins-official`) is added automatically at
startup. If it's missing — usually a blocked network — add it with
`/plugin marketplace add anthropics/claude-plugins-official`. The **community** marketplace
must always be added by hand: `/plugin marketplace add anthropics/claude-plugins-community`,
and its plugins install from the name `claude-community`.

Anthropic also maintains a **demo** marketplace of example plugins at `anthropics/claude-code`,
added by hand. Note the name mismatch: you add `anthropics/claude-code`, but its plugins
install from the marketplace name `claude-code-plugins` — e.g.
`/plugin install commit-commands@claude-code-plugins`. It's the fastest way to show someone
what the plugin system can do.

Managing marketplaces afterward: `/plugin marketplace list`, `... update <name>`,
`... remove <name>`. **Removing a marketplace uninstalls every plugin installed from it**,
so confirm before suggesting it.

## Installing plugins

```
/plugin install <plugin-name>@<marketplace-name>
```

This opens the plugin's detail view so the user can pick a scope. To skip the interactive
step entirely, use the CLI form, which defaults to user scope:

```bash
claude plugin install formatter@your-org --scope project
```

| Scope | Where it's written | Use when |
| :--- | :--- | :--- |
| `user` | `~/.claude/settings.json` | You want it everywhere, for yourself |
| `project` | the repo's `.claude/settings.json` | Every collaborator should get it |
| `local` | the repo's `.claude/settings.local.json` | Just you, just this repo |

There's also **managed** scope, pushed by an administrator through managed settings. Those
can't be changed by the user, so if a plugin won't disable, check whether it's managed.

`plugin-name` is the `name` from the **marketplace entry**, which can differ from the `name`
inside the plugin's own `plugin.json`. When a disable or uninstall mysteriously reports
"already disabled", a name mismatch on an older version is the usual cause.

### After any install, enable, or disable

```
/reload-plugins
```

Nothing takes effect in the running session until this runs (or the user restarts). The
summary it prints counts only each plugin's `commands/` directory under "skills", so
`0 skills` does **not** mean the plugin's `skills/` folder failed to load — don't diagnose
off that number.

Plugin skills are **namespaced by the plugin name**, so `commit-commands` provides
`/commit-commands:commit`, not `/commit`. When a user says a freshly installed skill "isn't
there", check whether they're typing the bare name before diagnosing anything else.

Installing a plugin that declares dependencies auto-installs them, and the install output
lists what came along.

Reloading has a real token cost: newly loaded components get appended to the conversation.
If the plugin ships MCP servers whose tools aren't deferred by tool search, the reload
invalidates the prompt cache and re-reads the whole conversation, so recent versions warn
and refuse until you pass `--force`. Mention this when a user is toggling plugins repeatedly
mid-session — batching the changes and reloading once is cheaper.

## Managing what's already installed

```
/plugin                       # interactive manager: Discover / Installed / Marketplaces / Errors
/plugin list                  # non-interactive; --enabled or --disabled to filter
/plugin disable <name>@<mkt>
/plugin enable  <name>@<mkt>
/plugin uninstall <name>@<mkt>
```

`/plugin disable`, `enable`, and `uninstall` all open the panel and leave it open — the user
presses Esc before typing anything else. For anything scripted, use `claude plugin ...` with
`--scope`.

The panel has four tabs — **Discover**, **Installed**, **Marketplaces**, **Errors** — cycled
with **Tab** and **Shift+Tab**.

In the **Installed** tab, problems sort to the top, `f` favorites, typing filters. A
**Not used recently** group collects marketplace plugins untouched for two weeks across at
least ten sessions — a good place to point someone whose startup feels bloated. Theme,
output-style, monitor, and workflow plugins are never listed there, since they deliver
value without being invoked.

To see exactly what a plugin contributes — commands, skills, agents, hooks, MCP servers, LSP
servers — without opening the panel:

```bash
claude plugin details <name>
```

It also prints the projected token cost. Before installing, the same inventory shows in the
detail view's **Will install** section, alongside a **Context cost** estimate and **Last
updated** (all version-gated — see the table in `references/troubleshooting.md`). Local and
custom marketplaces often don't supply that data, and you'll see "Components will be
discovered at installation" instead — that's normal, not a broken plugin.

Uninstalling a plugin that a project's `.claude/settings.json` enables asks which you mean:
disable it for yourself (writes an override to `.claude/settings.local.json`) or remove it
for everyone (edits the shared file). That's a shared-file edit — worth flagging to the user.

## Inspecting state without running anything

Everything about the installed state is on disk. Read these instead of asking the user to
run commands:

| File | What it tells you |
| :--- | :--- |
| `~/.claude/settings.json` | `enabledPlugins` map and `extraKnownMarketplaces` |
| `~/.claude/plugins/known_marketplaces.json` | Every marketplace, its source, and its install location |
| `~/.claude/plugins/installed_plugins.json` | Per-plugin scope, **installPath**, version, install/update timestamps |
| `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` | The copied plugin files — loaded for git/URL sources, but can be stale and unused for directory sources |
| a repo's `.claude/settings.json` | Project-scoped plugins and team marketplaces |

`installPath` is authoritative for cache-loaded plugins, and a mismatch with where the user
is editing is usually the bug. It is **not** the last word for directory-source marketplaces
— a skill's reported **Base directory** outranks it. See
[Developing a local plugin](#developing-a-local-plugin).

## Developing a local plugin

This trips people up constantly, so check it before debugging anything else.

A `directory`-source marketplace is read **in place**, but the plugin itself is **copied**
into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` at install time — **but
don't assume that's what's actually loaded.** Verify before diagnosing anything, because the
two cases need opposite fixes.

**Find out where the live copy is reading from.** When a skill is invoked, Claude Code prints
its **Base directory** in the injected content. That is ground truth for that skill, and it
outranks the `installPath` in `installed_plugins.json`. Cross-check with:

```bash
ls ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/skills/
```

Observed for a `directory`-source marketplace on this machine: the cache directory held only
one of the plugin's three skills, while all three were live and reported a Base directory
inside the source tree, not the cache. `${CLAUDE_PLUGIN_ROOT}` — which is expanded when the
skill is injected — resolved to the source tree as well. So for directory sources, skills can
load in place from the source, and the cache copy is simply stale and irrelevant.

Which fix you need follows from that:

| Loading from | Symptom | Fix |
| :--- | :--- | :--- |
| The source tree | Edits are on disk but the session shows old text | Try `/reload-plugins` first — a reinstall shouldn't be needed. Fall back to `/plugin marketplace update <mkt>` if the body is still stale |
| The cache | Edits to the source genuinely do nothing | `/plugin marketplace update <mkt>` then `/reload-plugins` |

Either way, **skill content is snapshotted into the session at startup**, so editing a file
never changes the running session on its own — even when the session loads from your source
tree. A stale skill body is far more often a missing `/reload-plugins` than a cache problem.

If the plugin's `version` in `plugin.json` changed, the cache path changes with it, and a
`/plugin uninstall` + `/plugin install` cycle is the reliable way to land on the new path.

For a tight edit-test loop, skip installation altogether and launch against the source:

```bash
claude --plugin-dir "C:\path\to\my-plugin"
```

When a plugin is loaded from its cache copy, any path reaching outside its own directory will
break after install even though it worked with `--plugin-dir`. Use `${CLAUDE_PLUGIN_ROOT}`
for internal paths.

## Team and project configuration

Commit this to a repo's `.claude/settings.json` so collaborators get prompted to install:

```json
{
  "extraKnownMarketplaces": {
    "my-team-tools": {
      "source": { "source": "github", "repo": "your-org/claude-plugins" }
    }
  },
  "enabledPlugins": { "formatter@my-team-tools": true }
}
```

Enabling a plugin in project settings does not install it. A plugin from an external source
stays uninstalled — and Claude Code reports it as such with the `claude plugin install`
command to run — until each team member installs it.

## Auto-updates

Marketplaces refresh in the background after startup with a random delay of up to ten
minutes, so the running session keeps whatever it launched with; a notification prompts for
`/reload-plugins`. Official marketplaces default to auto-update on, third-party and local
ones default to off. Toggle per marketplace in `/plugin` → **Marketplaces**, or set
`"autoUpdate": true` on an `extraKnownMarketplaces` entry in managed settings.

`DISABLE_AUTOUPDATER=1` turns off everything including Claude Code itself; add
`FORCE_AUTOUPDATE_PLUGINS=1` to keep plugin updates while pinning Claude Code.

## Security

Plugins execute arbitrary code with the user's privileges, and Anthropic doesn't verify
third-party plugin contents. When someone is about to add an unfamiliar marketplace or
install an unfamiliar plugin, say so once, plainly — then respect their decision.

Not all sources carry the same risk, so calibrate the warning:

| Source | What backs it |
| :--- | :--- |
| **Official** (`claude-plugins-official`) | Curated by Anthropic; inclusion is at their discretion |
| **Community** (`claude-community`) | Passed Anthropic's automated validation and safety screening, each entry pinned to a specific commit SHA. Safer than an arbitrary third party, but not Anthropic vouching for the code |
| **Anything else** | Nothing. Judge it on the source, and say so before an install |

Organizations can restrict all of this centrally with managed marketplace settings and
`strictKnownMarketplaces`.

## Reference files

- `references/troubleshooting.md` — symptom-to-fix table for plugins that won't load, skills
  that don't appear, language servers that won't start, and the version-gated behaviors that
  explain "it works on my machine". Read this whenever something isn't working.
- `references/official-catalog.md` — what's in the official Anthropic marketplace, including
  the language/plugin/binary table for code intelligence. Read this when recommending a
  plugin or setting up LSP.
