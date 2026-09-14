"""Unit tests for claude_plugin/mcp_server.py's two tools, called directly as
plain async functions (FastMCP's @mcp.tool() decorator leaves the underlying
function callable) against a tmp_path workspace — no MCP wire protocol, no
stdio subprocess. Mirrors builder_platform/tests/test_efficiency_round.py's
approach to testing BuilderSession.do_instantiate/do_run_selftest.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "builder_platform"))

import builder_core  # noqa: E402
import mcp_server  # noqa: E402


def _run(coro):
    return asyncio.run(coro)


def test_instantiate_creates_project_and_env(tmp_path):
    result = _run(mcp_server.instantiate_boilerplate(
        project_name="Test Agent", workspace_dir=str(tmp_path)))
    assert "Project created at" in result
    project = builder_core.locate_active_project(tmp_path)
    assert project is not None
    assert (project / "config.py").is_file()
    assert (project / "graph.py").is_file()  # engine file copied verbatim
    assert (project / ".env").is_file()      # copied from .env.example


def test_instantiate_twice_in_same_workspace_is_rejected(tmp_path):
    _run(mcp_server.instantiate_boilerplate(
        project_name="Test Agent", workspace_dir=str(tmp_path)))
    second = _run(mcp_server.instantiate_boilerplate(
        project_name="Another Agent", workspace_dir=str(tmp_path)))
    assert second.startswith("ERROR:")
    assert "already exists" in second


def test_run_selftest_before_instantiate_errors(tmp_path):
    result = _run(mcp_server.run_selftest(workspace_dir=str(tmp_path)))
    assert result.startswith("ERROR:")
    assert "no project yet" in result


def test_run_selftest_honors_max_runs(tmp_path, monkeypatch):
    _run(mcp_server.instantiate_boilerplate(
        project_name="Test Agent", workspace_dir=str(tmp_path)))
    project = builder_core.locate_active_project(tmp_path)
    monkeypatch.setattr(builder_core, "run_selftest_gate",
                         lambda project_dir: (False, "forced fail for the test"))
    mcp_server._selftest_runs.pop(str(project), None)
    for _ in range(builder_core.MAX_SELFTEST_RUNS):
        result = _run(mcp_server.run_selftest(workspace_dir=str(tmp_path)))
        assert result.startswith("SELFTEST FAIL")
    over_budget = _run(mcp_server.run_selftest(workspace_dir=str(tmp_path)))
    assert over_budget.startswith("ERROR:")
    assert "validation limit reached" in over_budget


def test_run_selftest_pass_writes_marker(tmp_path, monkeypatch):
    _run(mcp_server.instantiate_boilerplate(
        project_name="Test Agent", workspace_dir=str(tmp_path)))
    project = builder_core.locate_active_project(tmp_path)
    monkeypatch.setattr(builder_core, "run_selftest_gate",
                         lambda project_dir: (True, "ok"))
    mcp_server._selftest_runs.pop(str(project), None)
    result = _run(mcp_server.run_selftest(workspace_dir=str(tmp_path)))
    assert result.startswith("SELFTEST PASS")
    assert builder_core.has_persisted_pass(project)
