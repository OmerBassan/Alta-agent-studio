"""FR96: every Core safety check is proven non-vacuous.

A check that has never been seen to fail is not evidence of anything. For each
check, this test disables it in a temporary copy of the package and runs the
Core suite against the copy: at least one test must fail. If none does, the
check is untested — the suite would stay green with the safety removed.

The real source tree is never modified. Runs one subprocess per check
(roughly five seconds each); set STUDIO_SKIP_MUTATION=1 to skip locally.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HARNESS = "studio/core/harness.py"

CHECKS = {
    "an effect a crash left started is reconciled": (
        "        results: list[tuple[str, Result]] = await self._reconcile_started_effects(episode, entry.compiled)",
        "        results: list[tuple[str, Result]] = []"),
    "confirmation is required": (
        '            if confirmation is None:\n                return _refused("effect", "confirmation_missing",',
        '            if False:\n                return _refused("effect", "confirmation_missing",'),
    "cross-tenant references are rejected": ('                if row["tenant"] != tenant:', "                if False:"),
    "a halting guard halts": ('            if guard.verdict == "halt":', "            if False:"),
    "success is a read-back": ("            verified = bool(check.ok)", "            verified = True"),
    "rules deny effects": ("        rule = denying_rule(cap.deny_rules, {**facts, **args})", "        rule = None"),
    "claimed actions need verified evidence": (
        '                        or evidence["kind"] != "effect_verified"):', "                        and False):"),
    "never-ask facts are refused": ("            if fact in policy.never_ask_facts:", "            if False:"),
    "repetition is a stall": (
        "            if signatures[_signature(request)] >= self.settings.stall_repeats:", "            if False:"),
    "arguments must match established facts": (
        "            if str(facts[inp.fact]).lower() != str(args[inp.name]).lower():", "            if False:"),
    "the first message carries the disclosure": ("        if self._first_message(episode):", "        if False:"),
    "effects can be suspended": ("        if effects_suspended:\n            return _refused",
                                 "        if False:\n            return _refused"),
    "goals come from the declared set": (
        "        if request.goal is not None and request.goal not in policy.goals:", "        if False:"),
    "a passed deadline resumes the episode": (
        "        for episode in self.store.due_pending(self.store.now()):", "        for episode in ():"),
}


@pytest.mark.skipif(os.environ.get("STUDIO_SKIP_MUTATION") == "1", reason="STUDIO_SKIP_MUTATION=1")
@pytest.mark.parametrize("check", sorted(CHECKS))
def test_disabling_the_check_fails_the_suite(check, tmp_path):
    original, disabled = CHECKS[check]
    copy = tmp_path / "repo"
    shutil.copytree(ROOT / "studio", copy / "studio", ignore=shutil.ignore_patterns("__pycache__", "*.db"))
    target = copy / HARNESS
    source = target.read_text(encoding="utf-8")
    assert source.count(original) == 1, f"the check '{check}' is no longer in {HARNESS} as written"
    target.write_text(source.replace(original, disabled), encoding="utf-8")
    env = {**os.environ, "STUDIO_SKIP_MUTATION": "1", "PYTHONPATH": str(copy)}
    result = subprocess.run([sys.executable, "-m", "pytest", "studio/tests/test_core.py", "-q", "-x",
                             "-p", "no:cacheprovider"], cwd=copy, env=env, capture_output=True, text=True)
    assert result.returncode != 0, f"with '{check}' disabled the Core suite still passed:\n{result.stdout[-500:]}"
