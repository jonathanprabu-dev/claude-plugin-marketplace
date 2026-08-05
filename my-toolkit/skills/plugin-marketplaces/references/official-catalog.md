# The official Anthropic marketplace

Marketplace name: `claude-plugins-official`. Added automatically at startup; browsable via
`/plugin` → **Discover**, or at https://claude.com/plugins.

Curated by Anthropic — inclusion is at Anthropic's discretion, and the in-app submission
forms feed the **community** marketplace (`anthropics/claude-plugins-community`, installed
under the name `claude-community`), not this one. To distribute independently, create your
own marketplace.

## Contents

- [Code intelligence (LSP)](#code-intelligence-lsp)
- [External integrations](#external-integrations)
- [Security](#security)
- [Development workflows](#development-workflows)
- [Output styles](#output-styles)

## Code intelligence (LSP)

These plugins wire up a Language Server Protocol connection so Claude gets automatic
diagnostics after every edit and real code navigation (definitions, references, hover types,
symbols, implementations, call hierarchies) instead of grep approximations.

**The plugin does not install the binary.** Install it separately, or the plugin shows
`Executable not found in $PATH` in the `/plugin` **Errors** tab.

| Language | Plugin | Binary required |
| :--- | :--- | :--- |
| C/C++ | `clangd-lsp` | `clangd` |
| C# | `csharp-lsp` | `csharp-ls` |
| Go | `gopls-lsp` | `gopls` |
| Java | `jdtls-lsp` | `jdtls` |
| Kotlin | `kotlin-lsp` | `kotlin-language-server` |
| Lua | `lua-lsp` | `lua-language-server` |
| PHP | `php-lsp` | `intelephense` |
| Python | `pyright-lsp` | `pyright-langserver` |
| Rust | `rust-analyzer-lsp` | `rust-analyzer` |
| Swift | `swift-lsp` | `sourcekit-lsp` |
| TypeScript | `typescript-lsp` | `typescript-language-server` |

For anything not listed, an LSP plugin can be written by hand — see the plugins reference on
LSP servers.

## External integrations

Pre-configured MCP servers, so no manual server setup:

- **Source control** — `github`, `gitlab`
- **Project management** — `atlassian` (Jira/Confluence), `asana`, `linear`, `notion`
- **Design** — `figma`
- **Infrastructure** — `vercel`, `firebase`, `supabase`
- **Communication** — `slack`
- **Monitoring** — `sentry`

MCP-heavy plugins are the ones with real per-turn context cost. Check the **Context cost**
line in the plugin's detail view before recommending several at once, and prefer MCP tool
search so tools are deferred rather than always loaded.

## Security

- **`security-guidance`** — reviews each change Claude makes for common vulnerabilities and
  instructs Claude to fix what it finds in the same session. Supports project-specific rules.

## Development workflows

- **`commit-commands`** — commit, push, and PR creation workflows
- **`pr-review-toolkit`** — specialized agents for reviewing pull requests
- **`agent-sdk-dev`** — tooling for building with the Claude Agent SDK
- **`plugin-dev`** — toolkit for creating plugins

## Output styles

- **`explanatory-output-style`** — educational commentary on implementation choices
- **`learning-output-style`** — interactive learning mode
