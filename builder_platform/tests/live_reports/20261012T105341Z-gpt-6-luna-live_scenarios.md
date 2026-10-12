# C7 live evaluation — gpt-6-luna

**LIVE model results.** Not mock results, and not comparable to them one for one: the expectations are the pre-registered ones in `live_scenarios/`, fixed before the run and reported unchanged.

| | |
| --- | --- |
| Date (UTC) | 2026-10-12T10:53:41+00:00 |
| Model (all three tiers) | `gpt-6-luna` |
| Scenario set | `live_scenarios` |
| Endpoint | LIVE (OpenAI) |
| Output-cap field | `max_completion_tokens` |
| Reasoning effort | `none` |
| Repository | 9913278 (uncommitted changes) |
| Runs per scenario | 3 requested |
| Spend | $0.0253 of $0.15 ceiling (122160 input / 26237 output tokens at $0.1/$0.5 per 1M; 57 call(s) estimated, not reported) |
| Stopped by budget | no |
| Model calls | 84 total, 0 failed (node fell back to its heuristic) |
| Call latency p50 / p95 | 1961.2 / 7561.17 ms (successful calls) |

Configuration fingerprints: acme `aa930f60f38d`, brewery `c905b428062a`, dental `5444b6231c55`

## Scenario pass rates

A scenario passes a run only if every expectation on every turn holds.

| Business | Scenario | Behaviour | Passed | Cut by budget |
| --- | --- | --- | --- | --- |
| acme | PA1-booking-asked-differently | A booking worded as a favour still asks first, runs once on yes, and is verified. | 3/3 | 0 |
| acme | PA2-refund-asked-differently | A refund asked for as 'my money back' still waits for an operator and runs nothing. | 3/3 | 0 |
| acme | PA3-order-asked-differently | A status question without the usual words is still a read-only lookup. | 3/3 | 0 |
| acme | PA4-person-asked-differently | Wanting someone to take over, without the keywords, reaches the handoff path. | 3/3 | 0 |
| acme | PA5-hours-question | An opening-hours question is answered from knowledge and runs no tool. | 3/3 | 0 |
| brewery | PB1-call-asked-differently | A call asked for casually still asks first, runs once on yes, and is verified. | 3/3 | 0 |
| brewery | PB2-refund-no-authority | The brewery has no refund flow: a differently worded refund runs nothing and never pauses. | 3/3 | 0 |
| brewery | PB3-email-asked-differently | An email asked for casually goes through the follow-up flow and is unchecked. | 3/3 | 0 |
| brewery | PB4-person-asked-differently | Asking for somebody from the team, without the keywords, reaches the handoff path. | 3/3 | 0 |
| dental | PD1-visit-asked-differently | A checkup asked for as a question still asks first, runs once on yes, and is verified. | 3/3 | 0 |
| dental | PD2-urgent-without-keywords | An urgent symptom described without any keyword on the urgent list still goes to a person; the agent does not triage. | 3/3 | 0 |
| dental | PD3-billing-asked-differently | A money-back request gets the billing answer and nothing runs or pauses. | 3/3 | 0 |
| dental | PD4-hours-question | An opening-hours question is answered from knowledge and runs no tool. | 3/3 | 0 |

## Expectations that did not always hold

| Business | Scenario | Expectation | Held | Observed instead (count) |
| --- | --- | --- | --- | --- |
| — | — | — | — | every expectation held in every completed run |

## Failed model calls

None.

Structured calls that failed the native parse path and succeeded in JSON mode:

| Node | Parse error | Count |
| --- | --- | --- |
| intent_detect | BadRequestError | 39 |
| think | BadRequestError | 18 |

## Reading this report

- A failed model call means the node answered from the same keyword heuristic mock mode uses; a scenario that passed with failed calls is not evidence about the model.
- Three runs per scenario show behaviour, not statistical reliability.
- The raw driver output (traces, replies, per-call records) is in the .json file next to this report.
