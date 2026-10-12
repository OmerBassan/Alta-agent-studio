"""C8: the correction-loop demonstration holds (mock mode, zero tokens).

Runs builder_platform/tests/correction_loop.py's loop and pins its evidence:
the wrong rule (dental book_visit without `state_changing`) is caught by the
two scenarios that depend on the patient's yes, the correction fixes them,
the full suite shows no regression, and the fingerprint moves with the
configuration (broken differs, fixed equals the baseline).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from correction_loop import TARGET, correction_loop  # noqa: E402


def test_correction_loop_is_demonstrated():
    r = correction_loop(log=lambda _line: None)
    assert r["ok"], r["problems"]
    assert set(r["broken"]["failures"]) == {"D1-booking-confirmed-then-verified",
                                            "D3-urgent-symptom-at-the-confirmation-is-not-consent"}
    assert "turn 1: tools_run: expected [], observed ['book_dental_visit']" in \
        r["broken"]["failures"]["D1-booking-confirmed-then-verified"]
    assert not r["retest"]["failures"]
    assert all(not res["failures"] for res in r["full"].values())
    fp = r["fingerprints"]
    assert fp["broken"] != fp["baseline"] and fp["fixed"] == fp["baseline"]
    assert TARGET == "dental"
