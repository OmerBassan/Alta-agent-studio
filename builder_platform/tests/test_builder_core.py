"""Unit tests for builder_core.py's two project-location helpers, added to
support claude_plugin/'s MCP server (locate_active_project — an explicit
workspace_dir argument) and guard hook (find_enclosing_project — no cwd
assumption, walks from the target file's own path). Pure path logic, no
LLM/SDK/MCP objects — same style as test_builder.py's write/read policy tests.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from builder_core import (  # noqa: E402
    ENGINE_FILES, find_enclosing_project, locate_active_project,
)


def _make_project(root, name="AgentX_20260716"):
    project = root / name
    project.mkdir()
    (project / "config.py").write_text("AGENT_NAME = 'x'\n", encoding="utf-8")
    (project / "graph.py").write_text("# engine\n", encoding="utf-8")
    return project


# --- locate_active_project (explicit start_dir, used by the MCP server) ------

def test_locate_active_project_start_dir_is_the_project_itself(tmp_path):
    project = _make_project(tmp_path)
    assert locate_active_project(project) == project


def test_locate_active_project_start_dir_is_the_workspace(tmp_path):
    project = _make_project(tmp_path)
    assert locate_active_project(tmp_path) == project


def test_locate_active_project_unrelated_dir_is_none(tmp_path):
    (tmp_path / "not_a_project").mkdir()
    assert locate_active_project(tmp_path) is None


def test_locate_active_project_ambiguous_workspace_is_none(tmp_path):
    _make_project(tmp_path, "First_20260101")
    _make_project(tmp_path, "Second_20260102")
    assert locate_active_project(tmp_path) is None


# --- find_enclosing_project (path-ancestry walk, used by the guard hook) ----

def test_find_enclosing_project_from_a_file_inside_the_project(tmp_path):
    project = _make_project(tmp_path)
    target = project / "prompts.py"  # need not exist yet (a Write target)
    assert find_enclosing_project(target) == project


def test_find_enclosing_project_from_a_nested_file(tmp_path):
    project = _make_project(tmp_path)
    target = project / "docs" / "faq.md"
    assert find_enclosing_project(target) == project


def test_find_enclosing_project_from_the_project_dir_itself(tmp_path):
    project = _make_project(tmp_path)
    assert find_enclosing_project(project) == project


def test_find_enclosing_project_bare_config_py_alone_is_not_enough(tmp_path):
    # A stray config.py with no recognizable engine file beside it must NOT
    # be mistaken for an Alta project — this is exactly the false-positive
    # risk of walking arbitrarily far up a real filesystem tree.
    decoy = tmp_path / "some_unrelated_dir"
    decoy.mkdir()
    (decoy / "config.py").write_text("SOME_UNRELATED_SETTING = 1\n", encoding="utf-8")
    assert find_enclosing_project(decoy / "file.py") is None


def test_find_enclosing_project_unrelated_tree_is_none(tmp_path):
    (tmp_path / "docs").mkdir()
    assert find_enclosing_project(tmp_path / "docs" / "readme.md") is None


def test_find_enclosing_project_recognizes_every_engine_file_marker(tmp_path):
    for name in ENGINE_FILES:
        d = tmp_path / f"proj_{name.replace('.py', '')}"
        d.mkdir()
        (d / "config.py").write_text("x = 1\n", encoding="utf-8")
        (d / name).write_text("# engine\n", encoding="utf-8")
        assert find_enclosing_project(d / "prompts.py") == d
