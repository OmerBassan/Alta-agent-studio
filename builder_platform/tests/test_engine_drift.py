"""Engine drift gate: every generated agent carries the engine byte-identical.

The architecture's core claim is that agents differ only in their domain
surfaces (config.py, tools.py, prompts.py, .env, corpus, README) while the
engine is shared. builder_core.ENGINE_FILES is the canonical list; this test
fails if any agent under Generated_Agents/ is missing an engine file or carries
a copy that differs from boilerplate/. Engine fixes go upstream into
boilerplate/ once and are re-copied, never patched per agent.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from builder_core import ENGINE_FILES  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
BOILERPLATE = REPO_ROOT / "boilerplate"
AGENTS_ROOT = REPO_ROOT / "Generated_Agents"


def _agents() -> list[Path]:
    return sorted(p for p in AGENTS_ROOT.iterdir() if p.is_dir() and (p / "config.py").is_file())


def test_at_least_one_generated_agent_exists():
    # Guards against the parametrized test below passing vacuously on zero agents.
    assert _agents(), f"no generated agents found under {AGENTS_ROOT}"


@pytest.mark.parametrize("agent", _agents(), ids=lambda p: p.name)
def test_engine_files_identical_to_boilerplate(agent: Path):
    missing = sorted(n for n in ENGINE_FILES if not (agent / n).is_file())
    drifted = sorted(
        n for n in ENGINE_FILES
        if (agent / n).is_file() and (agent / n).read_bytes() != (BOILERPLATE / n).read_bytes()
    )
    assert not missing and not drifted, (
        f"{agent.name}: engine files missing={missing} drifted={drifted}. "
        f"Re-copy them from boilerplate/; never edit engine files per agent."
    )


def _compile_errors(path: Path) -> str | None:
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as e:
        return f"{path.name}:{e.lineno}: {e.msg}"
    return None


@pytest.mark.parametrize("name", sorted(ENGINE_FILES))
def test_engine_file_compiles(name: str):
    # Some engine files (agent_sandbox.py) are imported by no test or selftest,
    # so a syntax error in them would otherwise ship unnoticed to every agent.
    assert _compile_errors(BOILERPLATE / name) is None


def test_compile_check_is_not_vacuous(tmp_path: Path):
    broken = tmp_path / "broken.py"
    broken.write_text('print(f"unterminated\n")\n', encoding="utf-8")
    assert _compile_errors(broken) is not None
