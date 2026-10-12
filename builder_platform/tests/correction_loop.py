# -*- coding: utf-8 -*-
"""C8 correction-loop demonstration. Mock mode, zero tokens.

A deliberately wrong business rule is caught by the cross-business evaluation,
the rule is corrected, the failing scenarios and then the full suite are
re-run, and the configuration fingerprint shows the change. Nothing in the
repository is modified: the loop works on a temporary copy of one agent.

    python builder_platform/tests/correction_loop.py        # exit 0 = loop shown

The wrong rule: the dental practice's `book_visit` flow loses its
`state_changing` property, so booking a chair no longer needs the patient's
yes. The engine still starts (a flow without properties is a legal, ungated
flow), so no startup check can catch it; only the evaluation, which states
what the business requires, can.

What this does NOT show: the correction is scripted, not found by an agent.
It shows that a configuration error is observable, attributable to a
configuration change, and correctable without regressions.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_driver import run_agent  # noqa: E402
from test_cross_business_eval import REPO, SPECS, check_turn  # noqa: E402

TARGET = "dental"
FLOW = "book_visit"
# Matched on the stripped line, so CRLF (a fresh Windows checkout) and LF agree.
WRONG_RULE_LINE = 'properties=frozenset({"state_changing"}),'


def run_suite(dirs: Dict[str, Path], only: Optional[Dict[str, Set[str]]] = None) -> dict:
    """Run each business's scenarios (or only the named ones) in its own process.
    Returns {business: {"sha": fingerprint, "ran": [ids], "failures": {id: [problems]}}}."""
    out = {}
    for biz, agent_dir in dirs.items():
        scenarios = [sc for sc in SPECS[biz]["scenarios"] if only is None or sc["id"] in only.get(biz, ())]
        reply = run_agent(agent_dir, {"conversations": [sc["turns"] for sc in scenarios]})
        failures = {}
        for sc, turns in zip(scenarios, reply["conversations"]):
            problems = [f"turn {i}: {p}" for i, (expect, turn) in enumerate(zip(sc["expect"], turns), 1)
                        for p in check_turn(expect, turn)]
            if problems:
                failures[sc["id"]] = problems
        out[biz] = {"sha": reply["config_sha256"], "ran": [sc["id"] for sc in scenarios], "failures": failures}
    return out


def _without_rule(original: bytes) -> bytes:
    lines = original.splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line.strip() == WRONG_RULE_LINE.encode()]
    if len(hits) != 1:
        raise RuntimeError(f"expected the line {WRONG_RULE_LINE!r} exactly once in the {TARGET} config, "
                           f"found {len(hits)}: the demo no longer matches the agent")
    return b"".join(lines[:hits[0]] + lines[hits[0] + 1:])


def correction_loop(log: Callable[[str], None] = print) -> dict:
    """Run the five phases. Returns the evidence and `ok`; `problems` lists every
    check that did not hold (empty when the loop was demonstrated)."""
    problems: list = []
    real_dirs = {biz: REPO / spec["agent_dir"] for biz, spec in SPECS.items()}
    real_config = real_dirs[TARGET] / "config.py"
    original = real_config.read_bytes()
    tmp_root = Path(tempfile.mkdtemp(prefix="c8-correction-"))
    try:
        copy = tmp_root / real_dirs[TARGET].name
        shutil.copytree(real_dirs[TARGET], copy, ignore=shutil.ignore_patterns("__pycache__", ".env"))
        dirs = {**real_dirs, TARGET: copy}
        config = copy / "config.py"
        total = sum(len(s["scenarios"]) for s in SPECS.values())

        log(f"1. Baseline: all {total} business scenarios, {TARGET} from a temporary copy of its agent")
        baseline = run_suite(dirs)
        base_fail = {b: r["failures"] for b, r in baseline.items() if r["failures"]}
        if base_fail:
            problems.append(f"baseline is not green: {base_fail}")
        log(f"   {total - sum(len(f) for f in base_fail.values())}/{total} passed; "
            f"{TARGET} fingerprint {baseline[TARGET]['sha'][:12]}")

        log(f"2. Wrong rule: remove `{WRONG_RULE_LINE}` from {TARGET} flow `{FLOW}` "
            f"(booking no longer needs the patient's yes)")
        config.write_bytes(_without_rule(original))
        broken = run_suite({TARGET: copy})[TARGET]
        log(f"   the agent still starts; fingerprint {broken['sha'][:12]}")
        if not broken["failures"]:
            problems.append("the suite did not catch the wrong rule")
        for sid, msgs in broken["failures"].items():
            log(f"   FAIL {sid}")
            for m in msgs:
                log(f"        {m}")

        log("3. Correction: restore the rule")
        config.write_bytes(original)
        if config.read_bytes() != real_config.read_bytes():
            problems.append("the corrected config is not byte-identical to the reviewed one")
        retest = run_suite({TARGET: copy}, only={TARGET: set(broken["failures"])})[TARGET]
        log(f"   re-ran the failing scenario(s) {retest['ran']}: "
            f"{'all pass' if not retest['failures'] else 'STILL FAILING ' + str(sorted(retest['failures']))}")
        if retest["failures"]:
            problems.append(f"the correction did not fix {sorted(retest['failures'])}")

        log(f"4. Full suite again: all {total} business scenarios")
        full = run_suite(dirs)
        regressions = {b: sorted(set(full[b]["failures"]) - set(baseline[b]["failures"])) for b in full}
        regressions = {b: r for b, r in regressions.items() if r}
        if regressions:
            problems.append(f"regressions after the correction: {regressions}")
        log(f"   {total - sum(len(r['failures']) for r in full.values())}/{total} passed; "
            f"regressions: {regressions or 'none'}")

        shas = {"baseline": baseline[TARGET]["sha"], "broken": broken["sha"], "fixed": full[TARGET]["sha"]}
        log("5. Fingerprints (" + TARGET + "): " + ", ".join(f"{k} {v[:12]}" for k, v in shas.items()))
        if shas["broken"] == shas["baseline"]:
            problems.append("the wrong rule did not change the fingerprint")
        if shas["fixed"] != shas["baseline"]:
            problems.append("the corrected config's fingerprint differs from the baseline's")
        log("   broken != baseline, fixed == baseline: the runs are attributable to the configuration they used"
            if not any("fingerprint" in p for p in problems) else "   FINGERPRINT CHECK FAILED")
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    if real_config.read_bytes() != original:
        problems.append("the real agent's config.py changed during the demo")
    log("RESULT: correction loop demonstrated" if not problems else "RESULT: NOT demonstrated: " + "; ".join(problems))
    return {"ok": not problems, "problems": problems, "baseline": baseline, "broken": broken,
            "retest": retest, "full": full, "fingerprints": shas}


if __name__ == "__main__":
    sys.exit(0 if correction_loop()["ok"] else 1)
