"""Test configuration for the studio package.

Tests never reach a model provider: credentials are removed before any test
module is imported, so the model port starts in mock mode. A test that needs a
live model must opt in explicitly and is skipped without one."""

import os
import shutil
from pathlib import Path

import pytest

for _var in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "STUDIO_MODEL"):
    os.environ.pop(_var, None)

BUSINESSES = Path(__file__).resolve().parents[1] / "businesses"


@pytest.fixture
def business_copy(tmp_path):
    """Copy a business directory so a test can edit its specification safely.

    Returns ``make(name, replace=[(old, new), ...]) -> path to specification``.
    Each replacement must match, so a test can never pass because its edit
    silently did nothing."""

    def make(name: str, replace: list[tuple[str, str]] = (), folder: str = "copy") -> Path:
        target = tmp_path / folder / name
        shutil.copytree(BUSINESSES / name, target)
        spec = target / "specification.toml"
        text = spec.read_text(encoding="utf-8")
        for old, new in replace:
            assert old in text, f"test edit did not match: {old!r}"
            text = text.replace(old, new, 1)
        spec.write_text(text, encoding="utf-8")
        return spec

    return make
