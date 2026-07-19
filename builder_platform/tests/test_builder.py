"""Builder regression tests: the write/read policy, the wholesale instantiate,
and the selftest gate — everything deterministic (no LLM in the loop).

The property under test: the builder agent can NEVER touch an engine file,
write outside its own generated project, or read the repo's secret-bearing
areas (builder_platform/.env, frozen generated agents' credentials) — and the two
privileged operations (copy, selftest) behave as deterministic platform code.
"""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import builder  # noqa: E402
from builder import (  # noqa: E402
    BuilderSession, ENGINE_FILES, REPO_ROOT, instantiate_project,
    read_denial, run_selftest_gate, sanitize_project_name, write_denial,
)


# --- write policy -------------------------------------------------------------

def test_write_denied_before_instantiate(tmp_path):
    assert write_denial(str(tmp_path / "config.py"), None) is not None


def test_write_allowed_only_inside_project(tmp_path):
    project = tmp_path / "AgentX_20260716"
    project.mkdir()
    assert write_denial(str(project / "config.py"), project) is None
    assert write_denial(str(project / "docs" / "faq.md"), project) is None
    assert write_denial(str(project / "gmail_auth.py"), project) is None
    # outside the project: boilerplate, skill, platform, sibling project
    assert write_denial(str(REPO_ROOT / "boilerplate" / "config.py"), project)
    assert write_denial(str(REPO_ROOT / "SKILL.md"), project)
    assert write_denial(str(REPO_ROOT / "platform" / "runtime.py"), project)
    assert write_denial(str(tmp_path / "Other_1" / "config.py"), project)


def test_engine_files_denied_even_inside_project(tmp_path):
    project = tmp_path / "AgentX"
    project.mkdir()
    for name in ENGINE_FILES:
        why = write_denial(str(project / name), project)
        assert why is not None and "engine file" in why


def test_path_traversal_out_of_project_denied(tmp_path):
    project = tmp_path / "AgentX"
    project.mkdir()
    sneaky = str(project / ".." / ".." / "SKILL.md")
    assert write_denial(sneaky, project) is not None


# --- read policy ---------------------------------------------------------------

def test_read_allowlist(tmp_path):
    ws = tmp_path / "session1"
    ws.mkdir()
    assert read_denial(str(REPO_ROOT / "references" / "Same_Turn_Pipeline.txt"), ws) is None
    assert read_denial(str(REPO_ROOT / "boilerplate" / "config.py"), ws) is None
    assert read_denial(str(REPO_ROOT / "integrations" / "README.md"), ws) is None
    assert read_denial(str(REPO_ROOT / "SKILL.md"), ws) is None
    assert read_denial(str(ws / "AgentX" / "config.py"), ws) is None
    # secret-bearing / out-of-bounds areas
    assert read_denial(str(REPO_ROOT / "platform" / ".env"), ws)
    assert read_denial(str(REPO_ROOT / "Generated_CLI_Agents"), ws)
    assert read_denial(str(REPO_ROOT.parent), ws)
    assert read_denial("", ws)  # Glob/Grep without an explicit path


# --- naming ---------------------------------------------------------------------

def test_sanitize_project_name():
    assert sanitize_project_name("pizza palace SDR!") == "PizzaPalaceSdr"
    with pytest.raises(ValueError):
        sanitize_project_name("!!")


# --- instantiate ----------------------------------------------------------------

def test_instantiate_copies_boilerplate_wholesale(tmp_path):
    dest = instantiate_project("Test Agent", tmp_path)
    assert dest.parent == tmp_path
    for name in ENGINE_FILES | {"config.py", "tools.py", "prompts.py", "selftest.py"}:
        assert (dest / name).is_file(), f"missing {name}"
    assert not (dest / "__pycache__").exists()
    assert not (dest / ".env").exists()          # secrets never copied
    assert (dest / ".gitignore").is_file()       # but the ignore rules are


def test_session_instantiates_once(tmp_path):
    s = BuilderSession("sess1", workspaces_root=tmp_path)
    out1 = asyncio.run(s.do_instantiate({"project_name": "Demo Agent"}))
    assert "Project created" in out1["content"][0]["text"]
    assert s.project_dir is not None and s.project_dir.exists()
    out2 = asyncio.run(s.do_instantiate({"project_name": "Demo Agent"}))
    assert "ERROR" in out2["content"][0]["text"]


def test_selftest_tool_requires_project(tmp_path):
    s = BuilderSession("sess2", workspaces_root=tmp_path)
    out = asyncio.run(s.do_run_selftest({}))
    assert "ERROR" in out["content"][0]["text"]


def test_bad_session_id_rejected(tmp_path):
    with pytest.raises(ValueError):
        BuilderSession("../evil", workspaces_root=tmp_path)


# --- the asking channel -------------------------------------------------------

def test_ask_user_question_tool_is_disallowed(tmp_path):
    # The client is a browser: the SDK's question tool renders as a bare tool
    # event and strands the turn. Asking happens ONLY via the alta:ask block.
    # Observed for real — the builder reached for it during a proof run.
    s = BuilderSession("sess3", workspaces_root=tmp_path)
    assert "AskUserQuestion" in s._options().disallowed_tools


def test_shell_tools_stay_disallowed(tmp_path):
    # Voice-only product: no terminal surface anywhere in the builder.
    s = BuilderSession("sess4", workspaces_root=tmp_path)
    disallowed = s._options().disallowed_tools
    for tool in ("Bash", "BashOutput", "KillShell"):
        assert tool in disallowed


# --- the gate (integration: real subprocess on a real boilerplate copy) --------

def test_selftest_gate_passes_on_fresh_boilerplate(tmp_path):
    dest = instantiate_project("GateCheck", tmp_path)
    passed, output = run_selftest_gate(dest, timeout_s=180)
    assert passed, f"fresh boilerplate selftest must pass:\n{output[-1500:]}"
    assert "SELF-TEST PASSED" in output
