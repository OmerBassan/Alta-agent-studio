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
- `.claude-plugin/plugin.json` `mcpServers` — bundles
  `claude_plugin/mcp_server.py`, a stdio MCP server exposing
  `instantiate_boilerplate`/`run_selftest`, both thin wrappers around
  `builder_platform/builder_core.py`. Declared INLINE in the manifest, never
  in a root `.mcp.json`: that path is also where Claude Code looks for
  project-scoped MCP config, and since this repo is its own plugin root the
  file would be loaded by both — and the project-scope loader does not
  substitute `${CLAUDE_PLUGIN_ROOT}`, so that load always fails.
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

`/plugin install` targets a marketplace-registered plugin — this repo isn't
one, and pointing it at a raw local path fails (`Marketplace "..." not
found`, and the space in "Alta 2.0" makes it worse: the path gets split on
whitespace). For a local, no-marketplace plugin, Claude Code has a separate
mechanism: the `--plugin-dir` CLI flag, which "loads your plugin directly
without requiring installation" (verified against the official plugin docs).
It's a `claude` launch flag, not a slash command — so it must be run from an
interactive terminal outside this session.

Launch from the directory you want the generated agent to land in, pointing
the flag at this repo:

```bash
cd /path/to/some/other/project    # NOT inside this repo — proves cwd-relative output
claude --plugin-dir "C:\Users\Omer Bassan\Desktop\Projects\Alta 2.0"
```

Then run `/alta-build` in that session. `${CLAUDE_PLUGIN_ROOT}` still
resolves to this repo (so `SKILL.md`/`skill_steps/`/etc. load correctly);
the generated project lands in the directory you launched from, not here.
