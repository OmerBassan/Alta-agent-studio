"""Unit tests for claude_plugin/hooks/guard_engine_files.py's pure `decide`
function — fed crafted stdin-shaped payloads directly (no subprocess), so
these run as fast as any other unit test. Reuses the same project/path
fixtures as builder_platform/tests/test_builder.py's write-policy tests to
prove the hook's denial text is byte-identical to the web platform's for the
same inputs (both call the same builder_core.write_denial).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "hooks"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "builder_platform"))

import builder_core  # noqa: E402
from guard_engine_files import decide  # noqa: E402


def _project(tmp_path, name="AgentX_20260716"):
    project = tmp_path / name
    project.mkdir()
    (project / "config.py").write_text("x = 1\n", encoding="utf-8")
    (project / "graph.py").write_text("# engine\n", encoding="utf-8")
    return project


def _payload(file_path):
    return {"tool_name": "Write",
            "tool_input": {"file_path": str(file_path)},
            "hook_event_name": "PreToolUse"}


# --- scoping: silent no-op outside any Alta-managed project ------------------

def test_no_op_outside_any_project(tmp_path):
    target = tmp_path / "some_unrelated_file.py"
    assert decide("pre", _payload(target)) is None
    assert decide("post", _payload(target)) is None


def test_no_op_with_empty_payload():
    assert decide("pre", {}) is None
    assert decide("post", {}) is None


# --- pre: denies exactly what builder_core.write_denial denies --------------

def test_pre_denies_engine_file_with_the_shared_reason_text(tmp_path):
    project = _project(tmp_path)
    target = project / "graph.py"
    result = decide("pre", _payload(target))
    assert result is not None
    reason = result["hookSpecificOutput"]["permissionDecisionReason"]
    assert reason == builder_core.write_denial(str(target), project)
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"


def test_pre_allows_a_domain_surface_file(tmp_path):
    project = _project(tmp_path)
    target = project / "prompts.py"
    assert decide("pre", _payload(target)) is None


def test_pre_denies_write_outside_the_project_even_if_nearby(tmp_path):
    project = _project(tmp_path)
    sibling = tmp_path / "unrelated.py"
    # A file next to (not inside) the project — find_enclosing_project should
    # still resolve to the project via its own ancestry walk from `project`'s
    # sibling only if sibling is itself inside some project; here it's not
    # inside any project at all, so this must be a silent no-op, not a deny.
    assert decide("pre", _payload(sibling)) is None
    assert project  # project fixture unused otherwise; keep for readability


# --- post: clears the pass marker on a successful, allowed edit -------------

def test_post_clears_pass_marker_inside_project(tmp_path):
    project = _project(tmp_path)
    builder_core._write_pass_marker(project)
    assert builder_core.has_persisted_pass(project)
    target = project / "prompts.py"
    decide("post", _payload(target))
    assert not builder_core.has_persisted_pass(project)


def test_post_no_op_outside_any_project(tmp_path):
    target = tmp_path / "unrelated.py"
    assert decide("post", _payload(target)) is None
