# -*- coding: utf-8 -*-
"""The alta-builder MCP server: bundled with the Claude Code plugin, exposes
the same two privileged operations the web platform's SDK-MCP tools wrap
(`instantiate_boilerplate`, `run_selftest`) — both implemented by calling
straight into builder_platform/builder_core.py, the single shared engine.
Nothing here duplicates that logic; this file is protocol plumbing only.

Registered as a stdio server by the `mcpServers` block inside
`.claude-plugin/plugin.json`, auto-started by Claude Code whenever this
plugin is enabled — no manual `claude mcp add`. It is declared inline in the
manifest rather than in a root `.mcp.json` on purpose: that filename is ALSO
the project-scope MCP location, and this repo is its own plugin root, so a
root `.mcp.json` gets loaded twice — once as a plugin (where
${CLAUDE_PLUGIN_ROOT} is substituted) and once as a project config (where it
is not, leaving a literal path and a dead server).

Every tool takes an explicit `workspace_dir` (absolute path) rather than
inferring one from the process's own cwd: a stdio MCP server's cwd is fixed
once at spawn time and is not a reliable proxy for "where the user is right
now" in their terminal. commands/alta-build.md is responsible for always
passing the session's own current-working-directory string on every call.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Dict

# builder_core.py lives in builder_platform/ as a flat sibling module (the
# existing convention in that directory — see builder.py's own imports).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "builder_platform"))
import builder_core  # noqa: E402

from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("alta-builder")

# Per-process, per-project selftest-run counters — mirrors BuilderSession's
# `_selftest_runs` (verification budget, not a debugging loop), keyed by
# resolved project path so two builds in two different directories in the
# same long-lived session don't share a budget.
_selftest_runs: Dict[str, int] = {}


@mcp.tool()
async def instantiate_boilerplate(project_name: str, workspace_dir: str) -> str:
    """Create the agent project: wholesale-copies the tested boilerplate
    into workspace_dir. Call ONCE, at the start of Step 4, with the agent's
    name and the current working directory. Never copy files yourself."""
    ws = Path(workspace_dir).resolve()
    existing = builder_core.locate_active_project(ws)
    if existing is not None:
        return (f"ERROR: project already exists at {existing} — this "
                f"workspace builds one agent; edit it instead.")
    try:
        dest = builder_core.instantiate_project(project_name, ws)
    except (ValueError, OSError) as exc:
        return f"ERROR: {exc}"
    # Deadlock fix, mirrors BuilderSession.do_instantiate: ship a fillable
    # .env, not just the template, so the operator has a per-agent place to
    # put OPENAI_API_KEY.
    env_example = dest / ".env.example"
    env_file = dest / ".env"
    if env_example.is_file() and not env_file.exists():
        shutil.copyfile(env_example, env_file)
    return (
        f"Project created at {dest} (exact copy of boilerplate/).\n"
        f"Editable domain surfaces: config.py, tools.py, prompts.py, "
        f"README.md, .env.example, corpus/new integration files. Engine files "
        f"AND selftest.py (fixed, config-derived) are read-only — the selftest "
        f"adapts to your config.py automatically, so never touch it.")


@mcp.tool()
async def run_selftest(workspace_dir: str) -> str:
    """Run the generated project's selftest.py in mock mode. The test is
    DOMAIN-AGNOSTIC and FIXED — it derives every check from config.py, so
    you NEVER edit it. The build is not done until this reports PASS."""
    ws = Path(workspace_dir).resolve()
    project_dir = builder_core.locate_active_project(ws)
    if project_dir is None:
        return "ERROR: no project yet — call instantiate_boilerplate first."
    key = str(project_dir)
    runs = _selftest_runs.get(key, 0)
    if runs >= builder_core.MAX_SELFTEST_RUNS:
        return (
            f"ERROR: validation limit reached ({builder_core.MAX_SELFTEST_RUNS} "
            f"runs for this project). Stop iterating — report plainly which "
            f"check failed and what you recommend; do not attempt more fixes.")
    _selftest_runs[key] = runs + 1
    passed, output = builder_core.run_selftest_gate(project_dir)
    if passed:
        builder_core._write_pass_marker(project_dir)
        return ("SELFTEST PASS — the agent's full scripted conversation and "
                "every invariant check are green.")
    return f"SELFTEST FAIL\n\n{output[-1200:]}"


if __name__ == "__main__":
    mcp.run()
