# Alta Builder — Claude Code plugin

Runs the same Agent Builder as the web platform (`builder_platform/`), but as
a native `/alta-build` slash command in an interactive Claude Code terminal
session — no browser, no FastAPI server.

## Single source, by design

Installing this plugin ships the **whole Alta repo**, not a trimmed copy.
That's deliberate: `SKILL.md`, `skill_steps/`, `boilerplate/`, `references/`,
`integrations/`, and the deterministic engine in
`builder_platform/builder_core.py` are the single source both this plugin
and the web platform read — an edit to any of them reaches both consumers
automatically, with nothing to keep in sync by hand. See
`.claude-plugin/plugin.json` (the plugin manifest lives at the repo root for
exactly this reason: `${CLAUDE_PLUGIN_ROOT}` then resolves to the same root
`SKILL.md` already assumes).

## What's here

- `commands/alta-build.md` — the `/alta-build` slash command.
- `.mcp.json` (repo root) — bundles `claude_plugin/mcp_server.py`, a stdio
  MCP server exposing `instantiate_boilerplate`/`run_selftest`, both thin
  wrappers around `builder_platform/builder_core.py`.
- `hooks/hooks.json` (repo root) + `claude_plugin/hooks/guard_engine_files.py`
  — a Pre/PostToolUse guard that denies a Write/Edit to a protected engine
  file, scoped to only fire inside a recognized Alta-generated project (it's
  a silent no-op everywhere else in your Claude Code usage).

## Local setup

The bundled MCP server and hook both run as `python <script>.py`. Whatever
`python` resolves to on your PATH needs this repo's `requirements.txt`
installed (specifically: `mcp`, plus the stdlib-only pieces `builder_core.py`
uses — no `claude-agent-sdk` needed for this surface).

```bash
pip install -r requirements.txt
```

## Local install (no marketplace listing)

Point Claude Code at this repo as a local plugin source, then enable
`alta-builder`. From a Claude Code session:

```
/plugin install "C:\Users\Omer Bassan\Desktop\Projects\Alta 2.0"
```

(Exact install command/flags depend on your installed Claude Code version —
see `claude plugin --help` or the in-app `/plugin` command if this differs.)

Once enabled, run `/alta-build` from **any** project directory — the
generated agent lands in that directory, not inside this repo.
