# -*- coding: utf-8 -*-
"""Session isolation: the platform suite never runs on a developer's credentials.

The suite is mock-only (zero tokens). The platform's entry modules (app,
builder, vapi_adapter, runtime) import env_bootstrap, which merges the
repo-root .env into os.environ, and a developer's .env may hold a live
OPENAI_API_KEY for the voice platform. Blanking the key per test module is not
enough: on Windows a blanked variable is dropped when a subprocess inherits
the environment, and the child's env_bootstrap loads the key again.

Set here, before any test module is imported, and inherited by every
subprocess:
  * ALTA_SKIP_DOTENV=1: env_bootstrap reads no .env file on import;
  * OPENAI_API_KEY / OPENAI_BASE_URL removed: a key exported in the shell for
    a live run (live_eval.py, not a pytest test) does not reach the suite.
Tests that need a key set a fake one themselves (monkeypatch).
"""

import os

os.environ["ALTA_SKIP_DOTENV"] = "1"
for _name in ("OPENAI_API_KEY", "OPENAI_BASE_URL"):
    os.environ.pop(_name, None)
