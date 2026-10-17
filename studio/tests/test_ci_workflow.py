"""Story 1.12: the CI workflow stays credential-free and runs the full set.

The workflow's safety properties (no secret, no live model call, no step that
may fail silently, no narrowed trigger) are asserted here rather than left to a
comment in the YAML, so an edit that breaks them fails locally and in CI.
Checks are textual so the test needs no YAML parser beyond the pinned
requirements.
"""

import re
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"

REQUIRED_RUNS = [
    "python -m pip install -r requirements.txt",
    "python -m pytest studio/tests -q",
    "python -m studio scenarios --today 2026-10-13",
    "python -m pytest builder_platform/tests -q",
    "python -m pytest claude_plugin/tests -q",
]
SELFTEST_DIRS = ["boilerplate", "Generated_Agents/BassanBrewerySDR", "Generated_Agents/BrightSmileDental"]
BLANKED = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "ANTHROPIC_API_KEY")


@pytest.fixture(scope="module")
def text() -> str:
    assert WORKFLOW.is_file(), f"missing {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def _run_lines(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^\s*(?:-\s*)?run:\s*(.+)$", text, re.MULTILINE)]


def _job_env(text: str) -> str:
    match = re.search(r"^    env:[ \t]*\n((?:      \S.*\n)+)", text, re.MULTILINE)
    assert match, "no job-level env: block"
    return match.group(1)


def test_no_secret_is_referenced(text):
    assert "secrets." not in text
    assert "secrets[" not in text


def test_no_live_model_call(text):
    assert "--live" not in text


def test_credentials_are_blanked_at_job_level(text):
    job_env = _job_env(text)
    for var in BLANKED:
        assert re.search(rf'^      {var}:\s*""\s*$', job_env, re.MULTILINE), f"{var} not blanked in job env"
        assert len(re.findall(rf"\b{var}\b", text)) == 1, f"{var} set more than once"


def test_no_value_comes_from_variables_or_env_expressions(text):
    assert not re.search(r"\$\{\{\s*vars\.", text)
    assert not re.search(r"\$\{\{\s*env\.", text)


def test_permissions_are_read_only(text):
    assert re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", text, re.MULTILINE)
    assert not re.search(r":\s*write\b", text)
    assert "write-all" not in text


def test_no_step_can_fail_silently(text):
    assert "continue-on-error" not in text
    assert "||" not in text, "a || fallback (|| true, || :, || echo) can mask a failure"
    assert not re.search(r"\bexit\s+0\b", text)
    assert not re.search(r"\bset\s+\+e\b", text)


def test_no_step_is_conditional(text):
    assert not re.search(r"^\s+if:", text, re.MULTILINE)


def test_mutation_proofs_are_not_skipped(text):
    assert "STUDIO_SKIP_MUTATION" not in text


def test_runs_on_both_line_ending_platforms(text):
    assert "ubuntu-latest" in text and "windows-latest" in text
    assert re.search(r"fail-fast:\s*false", text)


def test_checkout_line_endings_are_asserted(text):
    probes = [r for r in _run_lines(text) if "requirements.txt" in r and "win32" in r and "\\r\\n" in r]
    assert probes, "no step checks CRLF on Windows and LF elsewhere"
    position = text.index(probes[0])
    assert text.index("actions/checkout") < position < text.index("python -m pip install")


def test_triggers_on_push_and_pull_request(text):
    on = re.search(r"^on:[ \t]*\n((?:[ \t]+.*\n|[ \t]*\n)+)", text, re.MULTILINE)
    assert on, "no on: block"
    block = on.group(1)
    assert re.search(r'^  push:[ \t]*\n    branches:\s*\["\*\*"\][ \t]*$', block, re.MULTILINE)
    assert re.search(r"^  pull_request:[ \t]*$", block, re.MULTILINE)
    assert "branches" not in block.split("pull_request:", 1)[1], "pull_request must not be narrowed by branch"
    for narrowing in ("paths:", "paths-ignore:", "branches-ignore:"):
        assert narrowing not in text


def test_every_required_command_runs(text):
    runs = _run_lines(text)
    for command in REQUIRED_RUNS:
        assert command in runs, f"missing step: {command}"
    selftest_dirs = re.findall(r"working-directory:\s*(\S+)\s*\n\s*run:\s*python selftest\.py\s*$", text, re.MULTILINE)
    assert sorted(selftest_dirs) == sorted(SELFTEST_DIRS)
