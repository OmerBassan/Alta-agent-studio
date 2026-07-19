"""Deterministic tool-result compaction (crush + retrieve).       [ENGINE]

Large tool results (a search returning 200 rows) cost tokens on EVERY hop
that sees them: the ENRICH prompt, last_action grounding, and any future
ANSWER-tier turn that replays them. This module inverts the cost: keep only
the salient items in-context, offload the full list to an in-process store,
and let the model (or a Flow) pull the original back ON DEMAND via the
`retrieve_full_result` tool — you pay retrieval tokens only when they are
actually needed.

Patterns adapted from headroom (Apache-2.0, github.com/headroomlabs-ai/headroom)
— see references/Context_Compression.txt for the full pattern catalog:
  - CCR (Compress-Cache-Retrieve): salient subset + sentinel marker carrying
    a retrieval ref + a registered retrieval tool.
  - Hard preservation invariants: error items, rare status values, and
    first/last anchors are NEVER dropped, whatever the budget says.
  - Results that ARE errors are exempt from compaction entirely — the
    execution validator and failure node need them intact.
  - Compaction never raises: any internal error returns the input unchanged
    (a lost saving is safe; a crashed Act node is not).

Everything here is stdlib, deterministic, and zero-model. The store is
module-level and process-local — the same lifetime as one CLI session, which
is exactly the scope of the data it holds. It is a cache, not memory: nothing
in it survives the process, and nothing in it is ever written to disk.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import Counter, OrderedDict
from typing import Any, Dict

import config

logger = logging.getLogger(__name__)

# Sentinel key marking the "items were dropped here" placeholder appended to a
# crushed list. Anything iterating a crushed list with a uniform-schema
# expectation must skip it — use strip_sentinels().
SENTINEL_KEY = "_dropped"

# Fields whose values behave like a status/category — a RARE value in one of
# these is an outlier worth keeping (the 1 "failed" row in 200 "ok" rows is
# usually the whole reason the user asked).
_STATUS_FIELDS = ("status", "state", "level", "severity", "result", "outcome")

# Error-ish substrings for status values. Deliberately narrow: this matches
# short enum-like field values ("failed", "timeout"), not prose.
_ERROR_VALUES = ("error", "fail", "timeout", "denied", "rejected", "cancel", "expired")

# ref -> original list. Bounded FIFO: one CLI session never legitimately needs
# more than a handful of offloaded originals in flight.
_RESULT_STORE: "OrderedDict[str, list]" = OrderedDict()
_STORE_MAX = 32


def _ref_for(items: list) -> str:
    """Short stable ref for an offloaded list (content-addressed, so the same
    payload crushed twice reuses one store slot)."""
    blob = json.dumps(items, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()[:10]


def _keep_split(budget: int) -> tuple:
    """First/last split of the keep budget (~60/40). Both halves are >= 1 only
    when the budget allows — max() on BOTH halves would overshoot a budget of
    1 to 2 items (headroom shipped that exact bug; keep the guard)."""
    first = max(1, round(budget * 0.6))
    last = budget - first
    return first, max(0, last)


def _is_salient(item: Any, status_counts: Dict[str, Counter], n: int) -> bool:
    """Preservation invariants for one array item: truthy error field, an
    error-ish status value, or a rare status value (<10% of the array)."""
    if not isinstance(item, dict):
        return False
    if item.get("error"):
        return True
    for field in _STATUS_FIELDS:
        value = item.get(field)
        if not isinstance(value, str) or not value:
            continue
        lowered = value.lower()
        if any(kw in lowered for kw in _ERROR_VALUES):
            return True
        if status_counts[field][value] <= max(1, n // 10):
            return True
    return False


def _crush_list(items: list, max_items: int) -> list:
    """Crush one oversized list: salient items ∪ first-K ∪ last-K, original
    order preserved, plus one sentinel carrying the retrieval ref."""
    n = len(items)
    status_counts: Dict[str, Counter] = {
        f: Counter(i.get(f) for i in items if isinstance(i, dict) and isinstance(i.get(f), str))
        for f in _STATUS_FIELDS
    }
    first_k, last_k = _keep_split(max_items)
    keep = set(range(first_k)) | set(range(n - last_k, n))
    keep |= {i for i, item in enumerate(items) if _is_salient(item, status_counts, n)}

    ref = _ref_for(items)
    _RESULT_STORE[ref] = items
    _RESULT_STORE.move_to_end(ref)
    while len(_RESULT_STORE) > _STORE_MAX:
        _RESULT_STORE.popitem(last=False)

    kept = [items[i] for i in sorted(keep)]
    dropped = n - len(kept)
    marker = (f"<<{dropped} of {n} items omitted to save tokens — call the "
              f"retrieve_full_result tool with ref='{ref}' if you need them>>")
    kept.append({SENTINEL_KEY: marker} if isinstance(items[0], dict) else marker)
    return kept


def crush_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Compact every oversized list field in a HEALTHY tool result.

    Error results pass through untouched (never compress what the failure
    path needs to read), as does anything below the size threshold — the
    mock tools in this boilerplate never trip it. Never raises."""
    try:
        if not isinstance(result, dict) or result.get("error"):
            return result
        max_items = int(getattr(config, "COMPACTION_MAX_ITEMS", 12))
        out = dict(result)
        for key, value in result.items():
            if isinstance(value, list) and len(value) > max_items:
                out[key] = _crush_list(value, max_items)
                logger.info("compaction: %s.%s %d -> %d items",
                            result.get("tool", "?"), key, len(value), len(out[key]))
        return out
    except Exception:
        logger.exception("compaction failed; passing result through unchanged")
        return result


def strip_sentinels(items: Any) -> Any:
    """Filter compaction sentinels out of a (possibly crushed) list, so code
    that iterates expecting a uniform schema never chokes on the marker.
    Non-list input passes through unchanged."""
    if not isinstance(items, list):
        return items
    return [x for x in items
            if not (isinstance(x, dict) and SENTINEL_KEY in x)
            and not (isinstance(x, str) and x.startswith("<<") and "retrieve_full_result" in x)]


def retrieve_full_result(ref: str = "", **_) -> Dict[str, object]:
    """Tool: fetch the original uncompressed items behind a compaction ref.
    Registered in TOOL_REGISTRY; expose it as a Flow only if the domain's
    ANSWER tier genuinely needs to page through full result sets."""
    items = _RESULT_STORE.get(ref or "")
    if items is None:
        return {"tool": "retrieve_full_result", "ref": ref,
                "error": "unknown or expired ref",
                "summary": "That result is no longer available — please re-run the original request."}
    return {"tool": "retrieve_full_result", "ref": ref, "items": items,
            "summary": f"Retrieved all {len(items)} original items for ref {ref}."}
