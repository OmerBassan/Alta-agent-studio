# Integration: Tavily — Web Search

<!-- Promoted 2026-07-12. Wiring validated selftest-green (hook + structural +
     filler gates) + happy/missing-query path through the real graph. This is the
     reference LOCAL-API recipe: a keyed REST call, no MCP server, no OAuth. -->

## Metadata
- **id:** `tavily_search`
- **source system / API version:** Tavily Search API (`POST https://api.tavily.com/search`)
- **transport:** `vendor SDK` (`tavily-python`)  |  raw HTTPS (`requests`/`httpx`) — **no MCP server, no OAuth**
- **auth:** a Tavily **API key** (bearer/keyed) — **client owns this; recipe ships none**
- **entity IDs:** none — read-only search; results are `{title, url, content, score}`
- **stakes:** **none** — read-only. NEVER wrap search in a `confirm`/`hitl` gate.
- **wiring last validated:** 2026-07-12 (selftest-green: hook + structural + filler + happy/missing-query path)
- **live-validation:** per-client at implement-time (needs the client's API key)

## What it gives you
One flow, **`web_search`**: the agent searches the web for a free-text `query`
and the ENRICH tier phrases the answer + sources. Same-turn (no confirm), so it's
the fast read-only path. It's also the simplest possible integration — a keyed
HTTPS call — which makes it the template for any other keyed REST API.

## 1. Prerequisites (the Validate gate — confirm BEFORE implementing live)
- [ ] A **Tavily account + API key** (app.tavily.com; a free tier exists).
- [ ] `pip install tavily-python`  (or call the REST endpoint directly with `httpx`/`requests`).
- [ ] `TAVILY_API_KEY` available to the process.
- [ ] (Optional) chosen defaults: `search_depth` (`basic`|`advanced`), `max_results`, `topic` (`general`|`news`), include/exclude domains.

_No OAuth, no server, no token store — that's the point of this one._

## 2. config.py — FLOWS  *(paste into `FLOWS`)*
```python
"web_search": Flow(
    tool="web_search",
    slots=("query",),
    slot_prompts={"query": "what you'd like me to look up"},
    validators={"query": _validate_query},
    enrich=True,          # read-only, no confirm/hitl; phrase the results
),
```

## config.py — validator + NEXT_STEP_HINTS + FILLERS_BY_TOOL  *(paste; [CUSTOMIZE tone])*
```python
def _validate_query(value: str, _slots: dict) -> tuple[bool, str]:
    """Trim and require a non-trivial query (free text; no catalog grounding).
    Idempotent on a canonical query."""
    q = " ".join((value or "").split())
    if len(q) < 2:
        return False, "What would you like me to search for?"
    return True, q

# NEXT_STEP_HINTS entry:
"web_search": "Want me to dig deeper on any of those?",

# FILLERS_BY_TOOL entry — reword in THIS agent's voice:
"web_search": ["Let me look that up…", "Searching the web now…", "One sec — checking the latest on that…"],
```

Also add the mock `query` SLOT_EXTRACTOR (keys on a leading search trigger; live
mode's ANSWER tier extracts the query from context, including a bare follow-up):
```python
_SEARCH_LEAD = re.compile(
    r"^(?:can you |could you |please |)"
    r"(?:search(?: the web)?(?: for)?|look\s?up|find(?: out)?|google|"
    r"tell me about|what\s?is|what's|who\s?is|latest on|news about)\s+", re.IGNORECASE)

def _extract_query(text: str):
    m = _SEARCH_LEAD.match((text or "").strip())
    return (text.strip()[m.end():].strip(" ?.\t") or None) if m else None

# SLOT_EXTRACTORS["query"] = _extract_query
```

## 3. tools.py — LIVE tool body  *(the ship target)*
```python
import os
from tavily import TavilyClient

_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def web_search(query: str = "", **_) -> dict:
    try:
        r = _client.search(query=query, search_depth="basic", max_results=5, include_answer=True)
    except Exception as e:  # network / auth / quota
        return {"tool": "web_search", "error": str(e), "summary": "I couldn't complete that search."}
    results = [{"title": x.get("title"), "url": x.get("url"),
                "content": x.get("content"), "score": x.get("score")}
               for x in (r.get("results") or [])]
    answer = r.get("answer") or ""
    if answer:
        summary = answer
    elif results:
        summary = f"Top result: {results[0]['title']} ({results[0]['url']})."
    else:
        summary = "I didn't find anything on that."
    return {"tool": "web_search", "query": query, "answer": answer,
            "results": results, "summary": summary}
# TOOL_REGISTRY["web_search"] = web_search
```

## tools.py — thin mock stub  *(selftest substrate ONLY — not the product)*
```python
def web_search(query: str = "", **_) -> dict:
    q = (query or "").strip()
    if not q:
        return {"tool": "web_search", "error": "empty query",
                "summary": "I couldn't run that search — what would you like me to look up?"}
    results = [{"title": f"{q} — overview", "url": "https://example.com/a",
                "content": f"A concise overview of {q}.", "score": 0.94},
               {"title": f"More on {q}", "url": "https://example.com/b",
                "content": f"Further detail about {q}.", "score": 0.88}]
    answer = f"Here's what I found about {q}, drawn from a couple of sources."
    return {"tool": "web_search", "query": q, "answer": answer, "results": results, "summary": answer}
```

## selftest.py — HOOK_CHECKS additions  *(REQUIRED — keeps structural_preflight green)*
```python
("validator", "web_search", "query", "a", {}, False, "search for"),
("validator", "web_search", "query", "  eiffel   tower  height ", {}, True, "eiffel tower height"),
```

## Customize per client (the "little modification")
- `TAVILY_API_KEY`; `search_depth` (`advanced` for deeper/costlier), `max_results`, `topic`, include/exclude domains.
- The `FILLERS_BY_TOOL` tone — reword in the agent's voice.

## Gotchas / limits
- **Free-text query.** The mock extractor keys on a leading trigger ("search for X"); a bare follow-up won't fill the slot in mock. LIVE mode's ANSWER tier extracts the query from context, so this is a mock-only limitation — keep the SCRIPT phrased as "search for …".
- **Results interact with compaction (a feature).** `results` is a list — with `max_results > COMPACTION_MAX_ITEMS` (default 12) the healthy result is crushed to a salient subset + a `retrieve_full_result` ref. At `max_results=5` it's under the cap.
- **Read-only → never gate it.** No `confirm`/`hitl`. Wrapping search in a confirm gate is a design error.
- **Billing/credits.** Tavily bills per search; `advanced` depth costs more. For high volume add a tool-level query cache (the engine's RAG TTL cache is for the RETRIEVER, not tools).
- **Alternative integration point.** Tavily can instead back the **Agentic-RAG RETRIEVER**: swap `config.RETRIEVER` to call Tavily and return `[{id, title, text, score}]` for `RETRIEVAL_INTENTS` — use that when the client wants *grounded knowledge answers* rather than an explicit "search" action.
- **Mock coverage.** The stub covers the happy path + the empty-query failure only; real network/auth/quota errors are proven on the live path (step 3).
