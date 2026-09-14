"""Pins for the builder-efficiency round: skill split budgets, deterministic
builder bounds, the selftest cap, the .env deadlock fix, and the cached opener.

Run: python -m pytest builder_platform/tests/test_efficiency_round.py -q
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import builder as builder_mod  # noqa: E402
import runtime_supervisor  # noqa: E402
import vapi_control  # noqa: E402
from builder import (  # noqa: E402
    BUILDER_EFFORT, BUILDER_MAX_TURNS, MAX_SELFTEST_RUNS, PLATFORM_BRIEF,
    BuilderSession, has_persisted_pass, read_denial,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# --- the skill split ---------------------------------------------------------

STEP_FILES = ("step1_discovery.md", "step2_playbook.md",
              "step3_contract.md", "step4_build.md")
# step3 (4_000 -> 4_300) and step4 (6_000 -> 6_200) were raised when the
# objection (A-I-P) + tie-down surfaces landed: genuinely NEW authoring the
# contract/build steps must mandate, not slack. Both were paid for FIRST by
# tightening existing prose (step3 4_799 -> 4_144, step4 6_278 -> 6_124 after
# the additions) and by pushing field-level rules into the [CUSTOMIZE] blocks in
# boilerplate/config.py, which Agent A already reads while editing that file.
# Raise a budget only for new REQUIRED surface, never to avoid trimming — the
# split exists to cap per-phase reading cost. step4 (6_200 -> 6_450) was raised
# when agent_sandbox.py (the text-chat sandbox) landed as a new engine file the
# build step must know is write-blocked, same as every other engine file.
BUDGETS = {"SKILL.md": 5_000, "step1_discovery.md": 6_000,
           "step2_playbook.md": 4_000, "step3_contract.md": 4_300,
           "step4_build.md": 6_450}


def test_skill_core_is_slim_and_schedules_the_steps():
    """The 53.7KB monolith must never come back: the core stays under 5KB and
    carries the read schedule the brief's bootstrap points at."""
    skill = REPO_ROOT / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert skill.stat().st_size <= BUDGETS["SKILL.md"]
    assert "When to read what" in text
    for name in STEP_FILES:
        assert name in text, f"read schedule must name {name}"
    # The single most expensive sentence of the old skill is gone for good.
    assert "read it FIRST, every time" not in text
    assert "FIRST, every time" not in text


@pytest.mark.parametrize("name", STEP_FILES)
def test_step_files_exist_within_budget(name):
    path = REPO_ROOT / "skill_steps" / name
    assert path.is_file(), f"missing {path}"
    assert path.stat().st_size <= BUDGETS[name], (
        f"{name} is {path.stat().st_size}B — over its {BUDGETS[name]}B budget; "
        f"the split exists to CAP reading cost, trim it")


def test_step_files_are_readable_by_the_builder(tmp_path):
    """READ_ROOTS must cover skill_steps/ or the bootstrap dies on permissions."""
    ws = tmp_path / "ws"
    ws.mkdir()
    target = REPO_ROOT / "skill_steps" / "step1_discovery.md"
    assert read_denial(str(target), ws) is None


def test_platform_env_still_denied(tmp_path):
    """The platform's own secrets stay outside the builder's read surface.

    Names the real package directory: read_denial never touches the filesystem,
    so pointing at a path that does not exist would pass for the wrong reason.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    platform_dir = REPO_ROOT / "builder_platform"
    assert platform_dir.is_dir(), "fixture drifted: builder_platform/ not found"
    assert read_denial(str(platform_dir / ".env"), ws) is not None
    assert read_denial(str(REPO_ROOT / ".env"), ws) is not None


def test_platform_brief_is_small_and_bootstraps_the_split():
    assert len(PLATFORM_BRIEF) < 5_000
    assert "skill_steps" in PLATFORM_BRIEF
    # The old brief LICENSED narration with example phrases; the ban replaced it.
    assert "Running the tests" not in PLATFORM_BRIEF
    assert "NEVER narrate" in PLATFORM_BRIEF
    # Edit turns are spec, not improvisation: without this section a change
    # request re-runs the whole bootstrap read (references, scanning) — the
    # recurring "builder reads forever on a small edit" complaint.
    assert "Edit turns" in PLATFORM_BRIEF
    assert "no codebase scanning" in PLATFORM_BRIEF


# --- deterministic builder bounds -------------------------------------------

def test_effort_defaults_low_and_is_clamped():
    assert BUILDER_EFFORT in ("low", "medium")
    assert BUILDER_MAX_TURNS == 24
    assert MAX_SELFTEST_RUNS == 2


def test_options_carry_effort_and_max_turns(tmp_path):
    session = BuilderSession("optcheck", workspaces_root=tmp_path)
    opts = session._options()
    assert opts.effort == BUILDER_EFFORT
    assert opts.max_turns == BUILDER_MAX_TURNS


def test_effort_clamp_rejects_high():
    """A typo or an ambitious env value must degrade to 'low', never pass
    through — 'only medium or low, nothing more' is a hard rule."""
    src = Path(builder_mod.__file__).read_text(encoding="utf-8")
    assert 'not in ("low", "medium")' in src, \
        "the effort clamp was removed — BUILDER_EFFORT could reach 'high'"


# --- selftest cap + .env deadlock fix ---------------------------------------

def _session_with_project(tmp_path) -> BuilderSession:
    session = BuilderSession("captest", workspaces_root=tmp_path)
    project = tmp_path / "captest" / "agent"
    project.mkdir(parents=True)
    session.project_dir = project
    return session


def test_selftest_cap_refuses_third_run(tmp_path, monkeypatch):
    """Runs 1 and 2 execute; run 3 is refused WITHOUT running the gate —
    the builder must report, not ruminate."""
    session = _session_with_project(tmp_path)
    calls = []
    monkeypatch.setattr(builder_mod, "run_selftest_gate",
                        lambda project_dir: calls.append(1) or (False, "X" * 9000))
    for _ in range(2):
        asyncio.run(session.do_run_selftest({}))
    assert len(calls) == 2
    result = asyncio.run(session.do_run_selftest({}))
    assert len(calls) == 2, "third invocation must not reach the gate"
    text = result["content"][0]["text"]
    assert "limit" in text.lower()


def test_selftest_fail_tail_trimmed_to_1200(tmp_path, monkeypatch):
    session = _session_with_project(tmp_path)
    monkeypatch.setattr(builder_mod, "run_selftest_gate",
                        lambda project_dir: (False, "Y" * 9000))
    result = asyncio.run(session.do_run_selftest({}))
    text = result["content"][0]["text"]
    assert text.startswith("SELFTEST FAIL")
    assert text.count("Y") == 1200


def test_instantiate_creates_a_fillable_env(tmp_path, monkeypatch):
    """The deadlock fix: a generated agent ships with .env, not only the
    template — otherwise the operator has nowhere to put OPENAI_API_KEY and
    the agent demos in MOCK forever."""
    session = BuilderSession("envtest", workspaces_root=tmp_path)
    dest = tmp_path / "envtest" / "Agent_1"

    def fake_instantiate(name, workspace):
        dest.mkdir(parents=True)
        (dest / ".env.example").write_text("OPENAI_API_KEY=\n", encoding="utf-8")
        return dest
    monkeypatch.setattr(builder_mod, "instantiate_project", fake_instantiate)

    asyncio.run(session.do_instantiate({"project_name": "Agent 1"}))
    assert (dest / ".env").is_file()
    assert (dest / ".env").read_text(encoding="utf-8") == "OPENAI_API_KEY=\n"


# --- cached opener -----------------------------------------------------------

def _write_config(tmp_path, body: str) -> Path:
    agent = tmp_path / "agent"
    agent.mkdir(exist_ok=True)
    (agent / "config.py").write_text(body, encoding="utf-8")
    return agent


def test_opener_plain_literal_extracted(tmp_path):
    agent = _write_config(tmp_path, 'X = 1\nOPENER = "Hi, this is Acme — got a minute?"\n')
    assert runtime_supervisor.opener_from_config(agent) == \
        "Hi, this is Acme — got a minute?"


def test_opener_annotated_literal_extracted(tmp_path):
    agent = _write_config(tmp_path, 'OPENER: str = "Hello there — is this Dana?"\n')
    assert runtime_supervisor.opener_from_config(agent) == \
        "Hello there — is this Dana?"


@pytest.mark.parametrize("body", [
    'OPENER = f"Hi {name}"\n',                # f-string — not static
    'OPENER = "Hi " + "there"\n',             # concatenation — not static
    'OPENER = "   "\n',                       # whitespace — the TTS-wedge trap
    'OPENER = ""\n',                          # empty
    'OPENER = 42\n',                          # not a string
    'NOT_OPENER = "Hi"\n',                    # absent
    'def broken(:\n',                         # syntax error
])
def test_opener_refused_on_any_doubt(tmp_path, body):
    agent = _write_config(tmp_path, body)
    assert runtime_supervisor.opener_from_config(agent) is None


def test_opener_missing_dir(tmp_path):
    assert runtime_supervisor.opener_from_config(tmp_path / "nope") is None


def test_patch_body_omits_blank_first_message():
    """Never ship a blank/whitespace firstMessage — ' ' wedges Vapi's TTS
    queue silently (logged trap, cost a day)."""
    model = {"provider": "custom-llm", "url": "https://x/v1"}
    assert "firstMessage" not in vapi_control._patch_body(model, None)
    assert "firstMessage" not in vapi_control._patch_body(model, "   ")
    body = vapi_control._patch_body(model, " Hi, this is Acme — got a minute? ")
    assert body["firstMessage"] == "Hi, this is Acme — got a minute?"
    assert body["firstMessageMode"] == "assistant-speaks-first"
    assert body["model"] is model


# --- persisted selftest pass (survives a server restart) --------------------

def _project_with_surface(tmp_path) -> object:
    project = tmp_path / "agent"
    project.mkdir()
    for name in ("config.py", "tools.py", "prompts.py", "selftest.py"):
        (project / name).write_text(f"# {name} v1\n", encoding="utf-8")
    return project


def test_no_marker_means_not_persisted(tmp_path):
    project = _project_with_surface(tmp_path)
    assert has_persisted_pass(project) is False


def test_marker_written_on_pass_is_trusted(tmp_path, monkeypatch):
    project = _project_with_surface(tmp_path)
    session = BuilderSession("markertest", workspaces_root=tmp_path)
    session.project_dir = project
    monkeypatch.setattr(builder_mod, "run_selftest_gate",
                        lambda project_dir: (True, "ok"))
    asyncio.run(session.do_run_selftest({}))
    assert has_persisted_pass(project) is True


def test_marker_invalidated_by_surface_edit(tmp_path, monkeypatch):
    project = _project_with_surface(tmp_path)
    session = BuilderSession("markertest2", workspaces_root=tmp_path)
    session.project_dir = project
    monkeypatch.setattr(builder_mod, "run_selftest_gate",
                        lambda project_dir: (True, "ok"))
    asyncio.run(session.do_run_selftest({}))
    assert has_persisted_pass(project) is True

    # Simulate an edit to a domain surface: the marker must no longer verify,
    # even though nobody explicitly deleted it (the write-policy path deletes
    # it too, but this proves the hash check alone is sufficient).
    (project / "config.py").write_text("# config.py v2 — edited\n", encoding="utf-8")
    assert has_persisted_pass(project) is False


def test_reattach_restores_selftest_passed_from_marker(tmp_path, monkeypatch):
    """The actual bug this fixes: a fresh BuilderSession (new server process)
    for a session whose project already PASSed must not show the Call button
    as disabled just because selftest_passed defaults to False in memory."""
    workspace = tmp_path / "ws"
    project = workspace / "sess" / "SomeAgent_20260101_000000"
    project.mkdir(parents=True)
    for name in ("config.py", "tools.py", "prompts.py", "selftest.py"):
        (project / name).write_text(f"# {name}\n", encoding="utf-8")

    first = BuilderSession("sess", workspaces_root=workspace)
    first.project_dir = project
    monkeypatch.setattr(builder_mod, "run_selftest_gate",
                        lambda project_dir: (True, "ok"))
    asyncio.run(first.do_run_selftest({}))
    assert first.selftest_passed is True

    # A brand-new BuilderSession object, as a restarted server would create —
    # project_dir starts unset, selftest_passed starts False. start() also
    # connects a real ClaudeSDKClient; stub it so this stays a unit test of
    # the reattach logic, not an integration test of the SDK connection.
    class _FakeClient:
        async def connect(self):
            pass
        async def disconnect(self):
            pass
    monkeypatch.setattr(builder_mod, "ClaudeSDKClient", lambda options: _FakeClient())

    reattached = BuilderSession("sess", workspaces_root=workspace)
    assert reattached.selftest_passed is False
    asyncio.run(reattached.start())
    try:
        assert reattached.project_dir == project
        assert reattached.selftest_passed is True
    finally:
        asyncio.run(reattached.close())
