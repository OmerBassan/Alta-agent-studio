#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PreToolUse/PostToolUse guard for Write/Edit/MultiEdit, bundled with the
Claude Code plugin. Reuses builder_platform/builder_core.py's `write_denial`
— the SAME function the web platform's SDK permission callback calls — so a
Write to an engine file is denied with byte-identical wording on both
surfaces. Nothing here reimplements the policy; this file is I/O plumbing
(stdin JSON in, hook-decision JSON out) around that one shared function.

Scoping: this guard activates ONLY when the target file resolves (by walking
up its own path — see `find_enclosing_project`) into a recognized
Alta-generated project. Everywhere else, it is a silent no-op, so it never
interferes with anything else the developer does in their normal Claude Code
session. This is a deliberate difference from the web platform's Read/Glob/
Grep hard-block: that guard protects an unsupervised, non-technical remote
client in a multi-tenant context; this one supervises the SAME trusted
developer's own local session, so only the engine-file write guard is
ported — see claude_plugin/README.md for the full rationale.

Invoked as: python guard_engine_files.py {pre|post}   (see hooks/hooks.json)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "builder_platform"))
import builder_core  # noqa: E402


def decide(phase: str, payload: dict) -> Optional[dict]:
    """Pure decision function: phase ("pre"/"post") + the hook's stdin
    payload -> a hookSpecificOutput dict to print, or None for a silent
    no-op. Separated from stdin/stdout plumbing so it's directly
    unit-testable without spawning a subprocess."""
    file_path = (payload.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        return None
    target = Path(file_path)
    if not target.is_absolute():
        # Best-effort fallback only — real Claude Code tool payloads are
        # absolute in practice; this just avoids a hard crash if one isn't.
        target = Path.cwd() / target
    project_dir = builder_core.find_enclosing_project(target)
    if project_dir is None:
        return None  # not an Alta-managed project — never interfere

    if phase == "pre":
        reason = builder_core.write_denial(str(target), project_dir)
        if reason is None:
            return None
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }
    if phase == "post":
        # Any successful, allowed edit invalidates a prior selftest PASS —
        # mirrors BuilderSession._can_use_tool's "any edit invalidates the
        # gate" (an edit that WAS denied never reaches PostToolUse at all).
        builder_core._clear_pass_marker(project_dir)
        return None
    return None


def main() -> None:
    phase = sys.argv[1] if len(sys.argv) > 1 else "pre"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        payload = {}
    result = decide(phase, payload)
    if result is not None:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
