"""Story 1.12: the CI workflow stays credential-free and runs the full set.

The workflow's safety properties (no secret, no live model call, no step that
may fail silently) are asserted here rather than left to a comment in the YAML,
so an edit that breaks them fails locally and in CI. Checks are textual so the
test needs no YAML parser beyond the pinned requirements.
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


@pytest.fixture(scope="module")
def text() -> str:
    assert WORKFLOW.is_file(), f"missing {WORKFLOW}"
    return WORKFLOW.read_text(encoding="utf-8")


def _run_lines(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^\s*(?:-\s*)?run:\s*(.+)$", text, re.MULTILINE)]


def test_no_secret_is_referenced(text):
    assert "secrets." not in text
    assert "secrets[" not in text


def test_no_live_model_call(text):
    assert "--live" not in text


def test_credentials_are_blanked_at_job_level(text):
    for var in ("OPENAI_API_KEY", "OPENAI_BASE_URL"):
        assert re.search(rf'^\s+{var}:\s*""\s*$', text, re.MULTILINE), f"{var} not blanked"
        assert len(re.findall(rf"\b{var}\b", text)) == 1, f"{var} set more than once"


def test_permissions_are_read_only(text):
    assert re.search(r"^permissions:\s*\n\s+contents:\s*read\s*$", text, re.MULTILINE)
    assert "write" not in text.split("permissions:", 1)[1].split("jobs:", 1)[0]


def test_no_step_can_fail_silently(text):
    assert "continue-on-error" not in text
    assert "|| true" not in text
    assert "||true" not in text


def test_runs_on_both_line_ending_platforms(text):
    assert "ubuntu-latest" in text and "windows-latest" in text
    assert re.search(r"fail-fast:\s*false", text)


def test_triggers_on_push_and_pull_request(text):
    assert re.search(r"^on:\s*$", text, re.MULTILINE)
    assert re.search(r"^\s+push:", text, re.MULTILINE)
    assert re.search(r"^\s+pull_request:", text, re.MULTILINE)


def test_every_required_command_runs(text):
    runs = _run_lines(text)
    for command in REQUIRED_RUNS:
        assert command in runs, f"missing step: {command}"
    selftest_dirs = re.findall(r"working-directory:\s*(\S+)\s*\n\s*run:\s*python selftest\.py\s*$", text, re.MULTILINE)
    assert sorted(selftest_dirs) == sorted(SELFTEST_DIRS)
