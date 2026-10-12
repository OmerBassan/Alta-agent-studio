"""The live-only paraphrase scenarios (live_scenarios/) are well-formed.

pytest cannot RUN them (the keyword mock cannot classify paraphrases), so this
only guards the files themselves: known expectation keys, one expectation per
turn, an existing agent folder, and unique ids. A malformed file would
otherwise fail only after tokens were spent.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from live_eval import load_specs  # noqa: E402
from test_cross_business_eval import _KNOWN, REPO, SPECS  # noqa: E402

LIVE = load_specs(Path(__file__).resolve().parent / "live_scenarios")


def test_live_scenarios_cover_the_same_businesses_as_the_deterministic_suite():
    assert set(LIVE) == set(SPECS)
    for biz, spec in LIVE.items():
        assert spec["agent_dir"] == SPECS[biz]["agent_dir"] and (REPO / spec["agent_dir"]).is_dir()


@pytest.mark.parametrize("biz", sorted(LIVE))
def test_live_scenarios_are_well_formed(biz):
    ids = [sc["id"] for sc in LIVE[biz]["scenarios"]]
    assert len(ids) == len(set(ids)) and all(i.startswith("P") for i in ids)
    for sc in LIVE[biz]["scenarios"]:
        assert len(sc["expect"]) == len(sc["turns"]), f"{sc['id']}: one expectation per turn"
        for expect in sc["expect"]:
            assert set(expect) <= _KNOWN, f"{sc['id']}: unknown expectation key(s) {set(expect) - _KNOWN}"
