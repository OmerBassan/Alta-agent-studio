# -*- coding: utf-8 -*-
"""Deterministic, framework-agnostic builder engine: the single source shared
by the web platform (builder_platform/builder.py, via a headless Claude Agent
SDK session) and the Claude Code plugin (claude_plugin/, via a bundled MCP
server + guard hook, for an interactive terminal session).

Nothing here knows about the SDK, FastAPI, or Claude Code — it is pure
path/policy logic operating on explicit arguments, so both front doors get
identical behavior (and identical bugfixes) for free. Front-door-specific
concerns (system prompts, session state, SDK tool wiring, MCP protocol
plumbing, hook I/O) live in the consumers, never here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# --- configuration (one place, env-overridable) ------------------------------

REPO_ROOT = Path(os.environ.get(
    "ALTA_REPO_ROOT",
    Path(__file__).resolve().parent.parent,
)).resolve()
BOILERPLATE_DIR = REPO_ROOT / "boilerplate"
WORKSPACES_DIR = Path(os.environ.get("WORKSPACES_DIR", REPO_ROOT / "workspaces")).resolve()
# Shipped/pre-built agents (e.g. the demo) live here. Unlike a workspace — which
# holds a project ONE level down — a Generated_Agents entry IS the project dir
# (config.py sits directly in it), so a reviewer can call it by folder name.
GENERATED_AGENTS_DIR = Path(
    os.environ.get("GENERATED_AGENTS_DIR", REPO_ROOT / "Generated_Agents")).resolve()
SKILL_PATH = REPO_ROOT / "SKILL.md"

# The domain-agnostic selftest runs in ~7s mock; 120s is generous headroom for
# a slow machine or a cold import. (Was 10s while the gate was stubbed and never
# actually ran — too tight now that it does.)
SELFTEST_TIMEOUT_S = int(os.environ.get("SELFTEST_TIMEOUT_S", "120"))

# The selftest gate may run at most this many times per session (run + one
# fix-and-rerun). The gate is for VERIFICATION, not iterative debugging — a
# builder that needs a third run must report the failure, not ruminate on it.
MAX_SELFTEST_RUNS = int(os.environ.get("MAX_SELFTEST_RUNS", "2"))

# Files copied verbatim from boilerplate and NEVER edited per agent: the engine
# (runtime) PLUS the now domain-agnostic selftest.py — it derives every check
# from config.py, so a per-agent edit is never needed and only risks breaking
# the gate (the old demo-coupled test forced exactly that rewrite loop). The
# write policy enforces the rule the skill states as convention.
ENGINE_FILES = frozenset({
    "graph.py", "nodes.py", "schemas.py", "llm_client.py",
    "rag_subgraph.py", "compaction.py", "filler.py", "selftest.py",
    "agent_sandbox.py", "episode_trace.py", "authz.py",
})

# Read allowlist roots, relative to REPO_ROOT: what the architect legitimately
# consults. Everything else in the repo (builder_platform/, other sessions' workspaces,
# frozen generated agents with live credentials) is out of bounds.
READ_ROOTS = ("references", "boilerplate", "integrations", "skill_steps")
READ_FILES = ("SKILL.md", "SKILL_OVERVIEW.md", "IDEAS.md")


def _is_under(path: Path, root: Path) -> bool:
    """True if path is root or inside it (resolved, case-normalized)."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# --- pure policy functions (unit-testable, no SDK/MCP/hook objects) ----------

def write_denial(file_path: str, project_dir: Optional[Path],
                  relative_base: Path = REPO_ROOT) -> Optional[str]:
    """Why a Write/Edit to file_path must be denied, or None if allowed.

    `relative_base` anchors a non-absolute file_path (Claude Code tool
    payloads are absolute in practice, so this rarely fires) — defaulted to
    REPO_ROOT so every existing caller is unaffected; a caller with its own
    natural root (e.g. a plugin resolving against the invoker's workspace)
    may pass it explicitly instead.
    """
    if not file_path:
        return "no file_path given"
    if project_dir is None:
        return ("no project exists yet — call instantiate_boilerplate first; "
                "files may only be created inside the generated project")
    p = Path(file_path)
    if not p.is_absolute():
        p = relative_base / p
    if not _is_under(p, project_dir):
        return (f"writes are only permitted inside your generated project "
                f"({project_dir}) — {file_path} is outside it")
    if p.name in ENGINE_FILES:
        return (f"{p.name} is a protected engine file (or the fixed, "
                f"config-derived selftest), copied verbatim from boilerplate and "
                f"never edited per agent. Edit only the domain surfaces: "
                f"config.py, tools.py, prompts.py, README.md, .env/.env.example, "
                f"corpus files, or new integration files — the selftest adapts to "
                f"config.py automatically.")
    return None


def read_denial(file_path: str, workspace_dir: Path,
                 relative_base: Path = REPO_ROOT) -> Optional[str]:
    """Why a Read/Glob/Grep at file_path must be denied, or None if allowed."""
    if not file_path:
        return ("pass an explicit path under an allowed directory "
                "(references/, boilerplate/, integrations/, SKILL.md, or your workspace)")
    p = Path(file_path)
    if not p.is_absolute():
        p = relative_base / p
    if _is_under(p, workspace_dir):
        return None
    for root in READ_ROOTS:
        if _is_under(p, REPO_ROOT / root):
            return None
    rp = p.resolve()
    for name in READ_FILES:
        if rp == (REPO_ROOT / name).resolve():
            return None
    return (f"{file_path} is outside the allowed read surface: references/, "
            f"boilerplate/, integrations/, SKILL.md, and your own workspace")


def sanitize_project_name(raw: str) -> str:
    """Collapse a free-text agent name to a safe directory stem."""
    stem = re.sub(r"[^A-Za-z0-9]+", "", raw.strip().title())
    if not (3 <= len(stem) <= 48):
        raise ValueError(
            f"project_name must reduce to 3-48 alphanumeric chars, got {raw!r}")
    return stem


# --- deterministic platform operations ---------------------------------------

def discover_project(workspace_dir: Path) -> Optional[Path]:
    """The session's generated project inside its workspace, or None.

    A workspace holds ONE project (do_instantiate enforces it); anything with
    a config.py counts. Ambiguity (0 or 2+ candidates) resolves to None —
    guessing between leftovers is worse than reporting nothing.
    """
    if not workspace_dir.is_dir():
        return None
    candidates = [d for d in workspace_dir.iterdir()
                  if d.is_dir() and (d / "config.py").is_file()]
    return candidates[0] if len(candidates) == 1 else None


def locate_active_project(start_dir: Path) -> Optional[Path]:
    """start_dir IS a project (has config.py directly in it) or is a
    workspace holding exactly one project one level below.

    Needed anywhere a caller's notion of "current directory" may be EITHER
    the workspace that CONTAINS the generated project OR the project
    directory itself — e.g. a developer naturally `cd`s into the generated
    folder mid-session. discover_project alone only handles the former and
    would wrongly report "no project" (and, in a guard hook, wrongly ALLOW an
    engine-file edit) for the latter.
    """
    if (start_dir / "config.py").is_file():
        return start_dir
    return discover_project(start_dir)


def _looks_like_generated_project(candidate: Path) -> bool:
    """config.py alone is too weak a signature when walking arbitrarily far
    up a filesystem tree (an unrelated ancestor directory could coincidentally
    hold one) — require it alongside at least one recognizable engine file,
    since a real boilerplate-derived project always ships both together."""
    if not (candidate / "config.py").is_file():
        return False
    return any((candidate / name).is_file() for name in ENGINE_FILES)


def find_enclosing_project(target: Path) -> Optional[Path]:
    """Walk upward from `target` (a file or directory) looking for the
    nearest ancestor that IS a generated project. Returns None if none is
    found before the filesystem root.

    Used by the guard hook to decide "is this Write/Edit touching an
    Alta-managed project at all" from the target file's own absolute path —
    deliberately independent of any notion of the caller's current working
    directory (a hook subprocess's cwd, or whether the developer `cd`-ed
    around mid-session, is not a reliable signal; the file path itself is).
    """
    current = target if target.is_dir() else target.parent
    for candidate in (current, *current.parents):
        if _looks_like_generated_project(candidate):
            return candidate
    return None


def instantiate_project(project_name: str, workspace_dir: Path) -> Path:
    """Wholesale-copy boilerplate/ into the workspace. Platform code, not
    agent work — the copy is exact by construction."""
    stem = sanitize_project_name(project_name)
    dest = workspace_dir / f"{stem}_{time.strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(
        BOILERPLATE_DIR, dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env"),
    )
    return dest


# The domain surfaces that can change what selftest verifies. A hash over
# just these — not the whole tree — is what a persisted PASS is checked
# against, so an engine-file change (which the builder can't make anyway)
# never invalidates it, but any edit that could change behavior does.
_SELFTEST_SURFACE = ("config.py", "tools.py", "prompts.py", "selftest.py")
_MARKER_NAME = ".selftest_passed.json"


def _surface_hash(project_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in _SELFTEST_SURFACE:
        path = project_dir / name
        digest.update(name.encode())
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
    return digest.hexdigest()


def _write_pass_marker(project_dir: Path) -> None:
    marker = {"surface_hash": _surface_hash(project_dir)}
    (project_dir / _MARKER_NAME).write_text(json.dumps(marker), encoding="utf-8")


def _clear_pass_marker(project_dir: Path) -> None:
    (project_dir / _MARKER_NAME).unlink(missing_ok=True)


def has_persisted_pass(project_dir: Path) -> bool:
    """True if project_dir's own marker says PASS and nothing it covers has
    changed since — lets a session reattached after a server restart trust a
    prior selftest run instead of a stateless in-memory flag defaulting to
    False and disabling the call button on an agent that already proved out.
    """
    marker_path = project_dir / _MARKER_NAME
    if not marker_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return marker.get("surface_hash") == _surface_hash(project_dir)


def run_selftest_gate(project_dir: Path,
                      timeout_s: int = SELFTEST_TIMEOUT_S) -> tuple[bool, str]:
    """Run the generated agent's selftest.py in forced MOCK mode (no keys,
    no journal writes, fillers exercised). Returns (passed, output_tail)."""
    env = dict(os.environ)
    env.update({
        "OPENAI_API_KEY": "", "OPENAI_BASE_URL": "",   # force MOCK tiers
        "MEMORY_ENABLED": "0",                          # no journal writes
        "PYTHONIOENCODING": "utf-8",
    })
    try:
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", "selftest.py"],
            cwd=str(project_dir), env=env, timeout=timeout_s,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return False, f"selftest timed out after {timeout_s}s"
    tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:]
    return proc.returncode == 0, tail
