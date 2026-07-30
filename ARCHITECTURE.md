# Architecture — Alta Agent Studio

Three decisions define this system. Each is enforced by code or a test, not by
convention.

---

## 1. The Director Gate: a deterministic state machine, not an LLM graph

An outbound SDR must *lead* — open, qualify, handle objections, close — while
staying responsive to whatever the lead actually says. The obvious design is to
let the model decide the next move each turn. We rejected it.

**The call agenda is a cursor over a tuple of stages, advanced by structured
predicates.** No model call, no graph edge, no prose parsing.

```python
# boilerplate/config.py
CALL_ARC: Tuple[Stage, ...] = (
    Stage(name="discovery",
          objective="confirm you've reached the buyer and why the call matters",
          nudge="Are you the one who handles beverage purchasing?",
          advance_when={"agent_led_once": True}),
    Stage(name="qualify", flow="lead_profile",
          advance_when={"flow_complete": "lead_profile"}),
)
```

`advance_when` accepts only `flow_complete`, `session_fact`, `agent_led_once`,
or `intent_seen` — machine-checkable facts already in state. The cursor advance
is monotonic and bounded by the arc length ([`nodes.py`](boilerplate/nodes.py)
`_director`), so it cannot loop.

All five gates live **inside one node**, `validator_node` — the only door to the
user — in a load-bearing order:

```
_objection_gate → _director → _update_summary → stall detector → _tiedown
```

The objection gate runs first because its outcome decides whether the director
may speak an agenda move at all: a lead pushing back owns that turn, and an
agent that answers an objection *and* pivots in the same breath sounds like it
wasn't listening.

**Why this over a reactive LLM graph:**

| | Director gate | LLM-routed graph |
|---|---|---|
| Cost per turn | **0 tokens, 0 calls** | +1 model round-trip |
| Latency | ~0 ms | +200–800 ms on the reply path |
| Behavior under load | identical every call | drifts with temperature |
| Debugging a wrong move | read the cursor | re-read a prompt and hope |

That zero is the point: the director adds **nothing** to any row of the model-tier
budget. A voice agent's latency budget is spent on the tokens the caller actually
hears — never on deciding what to say next.

**Inbound/outbound is one switch.** `CALL_ARC = ()` makes the director a
documented no-op, and every gate above degrades with it. The same engine serves a
reactive support agent and a proactive SDR with no branching.

### Objection handling: Acknowledge → Isolate → Pivot, one turn, one owner each

| Step | Owner | Kind |
|---|---|---|
| Acknowledge | `_objection_ctx` — "validate in under six words, then answer in ONE sentence" | prompt |
| Isolate | `_objection_gate` — "Besides {topic}, anything else holding you back?" | code |
| Pivot | `_director` — the next agenda move | code |

The model never asks the question; the deterministic layer owns the turn's single
question. On an objection turn the help-desk tail is **replaced, not stacked**
([`prompts.py`](boilerplate/prompts.py)) — shipping two conflicting directives in
one payload is how a reply ends up with two questions or a limp non-answer.

---

## 2. TTFT and dead-air prevention

**Dead air is a correctness bug, not a performance nit.** A silent line reads as a
dropped call. Four mechanisms cover every stretch of silence a turn can produce:

1. **Pre-think filler.** A short token (`FILLER_THINKING`) is pushed onto the SSE
   stream the instant a turn arrives — *before* the graph runs — so first-token
   time is bounded by the network, not by inference.
2. **Debounced per-tool filler banks.** A tool filler is emitted only if the tool
   outlasts `FILLER_DELAY_MS`, so fast tools stay silent and slow ones get cover.
3. **Sentence-chunked replies.** The reply streams by sentence, so TTS starts
   speaking before generation finishes.
4. **A wall-clock ceiling.** If a turn exceeds `RUNTIME_TURN_TIMEOUT_S`, the
   runtime speaks a short apology rather than leaving the line open.

**Sync tools are offloaded, and the reason is subtle** ([`nodes.py`](boilerplate/nodes.py)
`tool_exec_node`):

```python
task = asyncio.ensure_future(asyncio.to_thread(fn, **args))   # sync tool
```

A blocking `smtplib` or `requests` call on the event loop doesn't merely slow the
turn — it freezes the loop, so **no timer can race it**: the filler queue stalls
*and* the dead-air ceiling can never fire. A hung socket becomes silence on a live
call. Offloading keeps the loop free to drain fillers and enforce the ceiling.

A pre-TTS sanitizer is the last hop, buffering across chunk boundaries so markdown
or a split URL never reaches the voice. It is a backstop: **text that needs the
sanitizer is treated as a defect upstream**, not a licensed shortcut.

---

## 3. Automated budgets: conversational discipline as a CI gate

Voice rules stated only in a prompt are advisory. Here they fail the build.

**Every generated agent must pass `selftest.py` before it can be served** — the
builder runs it as a subprocess gate and refuses to hand over a failing agent.

| Gate | Enforces | Failure |
|---|---|---|
| `voice_budget_preflight` | `OPENER` ≤ 20 words; no `FILLER_THINKING` token ends in `...` | long openers delay pickup; ellipses make TTS trail |
| `objection_preflight` | isolate ≤ `MAX_REPLY_WORDS // 2`; rebuttal + isolate ≤ `MAX_REPLY_WORDS`; `reply.count("?") == 1` | the isolate shares its turn with the rebuttal |
| `persona_preflight` | when `CALL_ARC` is non-empty, prompts must not say "support assistant" | an outbound agent that forgets it placed the call |
| `call_arc_preflight` | 6 behavioral cases on a *synthetic* arc | holds for every domain, not just the shipped one |
| `tiedown_preflight` | a tie-down that would exceed `MAX_REPLY_WORDS` is dropped | airtime is finite |

`MAX_REPLY_WORDS = 20` is a **constant measured by code**, not prose in a prompt:
the deterministic appenders count against it before emitting
([`config.py`](boilerplate/config.py)).

The platform suite (`python -m pytest builder_platform/tests/`, **161 tests**)
pins the builder itself: skill-file byte budgets, the per-message turn ceiling,
the selftest run cap, and the rule that a blank Vapi `firstMessage` is never
shipped — a single space silently wedges Vapi's TTS queue.

Both director gates are designed to pass on an **empty** arc, so the inbound
boilerplate stays green while the engine itself remains under test.

---

## Verify

```bash
python -m pytest builder_platform/tests/   # platform: 161 passed
cd Generated_Agents/<Agent> && python selftest.py   # per-agent gate, exit 0
```

Engine files (`graph.py`, `nodes.py`, `schemas.py`, `llm_client.py`, …) are copied
**verbatim** into every generated agent; only domain surfaces (`config.py`,
`tools.py`, `prompts.py`, selftest checks) are written per build. Engine fixes go
upstream once, never per agent.
