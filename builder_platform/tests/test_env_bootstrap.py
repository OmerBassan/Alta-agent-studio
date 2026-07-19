"""env_bootstrap merge-precedence + placeholder-filtering tests.

The property under test: credentials from the repo-root .env reach os.environ
(and therefore any spawned subprocess, per subprocess_cli.py which inherits
os.environ), root wins over legacy builder_platform/.env, real OS env wins over both,
and unfilled placeholders never reach os.environ as garbage values.
"""

import importlib
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import env_bootstrap  # noqa: E402


@pytest.fixture
def eb(tmp_path, monkeypatch):
    """A fresh env_bootstrap pointed at temp .env files, reloaded per test."""
    root_env = tmp_path / ".env"
    legacy_env = tmp_path / "platform" / ".env"
    legacy_env.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(env_bootstrap, "ROOT_ENV", root_env)
    monkeypatch.setattr(env_bootstrap, "LEGACY_PLATFORM_ENV", legacy_env)
    monkeypatch.setattr(env_bootstrap, "_LOADED", False)
    return env_bootstrap, root_env, legacy_env


def test_root_env_reaches_environ(eb, monkeypatch):
    mod, root_env, _ = eb
    monkeypatch.delenv("ALTA_TEST_KEY", raising=False)
    root_env.write_text("ALTA_TEST_KEY=from_root\n")
    mod.load_env(force=True)
    assert os.environ["ALTA_TEST_KEY"] == "from_root"


def test_root_wins_over_legacy(eb, monkeypatch):
    mod, root_env, legacy_env = eb
    monkeypatch.delenv("ALTA_TEST_KEY", raising=False)
    legacy_env.write_text("ALTA_TEST_KEY=from_legacy\n")
    root_env.write_text("ALTA_TEST_KEY=from_root\n")
    mod.load_env(force=True)
    assert os.environ["ALTA_TEST_KEY"] == "from_root"


def test_blank_root_does_not_shadow_legacy(eb, monkeypatch):
    """The two-file footgun: a blank in root must fall through to a real legacy
    value, not overwrite it with empty."""
    mod, root_env, legacy_env = eb
    monkeypatch.delenv("VAPI_TEST_SECRET", raising=False)
    legacy_env.write_text("VAPI_TEST_SECRET=real_secret\n")
    root_env.write_text("VAPI_TEST_SECRET=\n")
    mod.load_env(force=True)
    assert os.environ["VAPI_TEST_SECRET"] == "real_secret"


def test_placeholder_is_filtered(eb, monkeypatch):
    mod, root_env, _ = eb
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    root_env.write_text("ANTHROPIC_API_KEY=[PASTE_YOUR_ANTHROPIC_API_KEY_HERE]\n")
    mod.load_env(force=True)
    assert "ANTHROPIC_API_KEY" not in os.environ  # garbage never set


def test_real_os_env_wins_over_files(eb, monkeypatch):
    mod, root_env, _ = eb
    monkeypatch.setenv("ALTA_TEST_KEY", "from_real_os")
    root_env.write_text("ALTA_TEST_KEY=from_root\n")
    mod.load_env(force=True)
    assert os.environ["ALTA_TEST_KEY"] == "from_real_os"


def test_anthropic_key_status(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-abcd1234")
    usable, msg = env_bootstrap.anthropic_key_status()
    assert usable and "1234" in msg
    monkeypatch.setenv("ANTHROPIC_API_KEY", "[PASTE_YOUR_ANTHROPIC_API_KEY_HERE]")
    usable, msg = env_bootstrap.anthropic_key_status()
    assert not usable and "not set" in msg
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    usable, _ = env_bootstrap.anthropic_key_status()
    assert not usable
