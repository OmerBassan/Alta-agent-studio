# Epic 9 Context: Prove it generalises

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Test the product's thesis by its own falsifiers rather than by assertion. All four exemplar businesses (brewery: 40-person event; gym: two-month membership freeze; garden centre: dying plant; dental practice: root-canal explanation) are built through the Builder by the path a real operator would take. Engine leaks, resolution-model strain, setup effort, the validity floor and the episode cost slope are recorded and reported. At least one real business runs end to end on real inbound mail, and two or three real operator conversations test the premise that operators can put their tacit rules into words. V1 is not complete without this epic. It is the one that can falsify the architecture claim (only the business layer changes between businesses) and the usefulness claim. The four exemplar specifications are constructions, not any real business's rules. That makes them an adequate substitute for the architecture claim only.

## Stories

- Story 9.1: Fix the engine-leak classification rules before the fourth business
- Story 9.2: The first exemplar business through the Builder
- Story 9.3: The second exemplar business through the Builder
- Story 9.4: The third exemplar business through the Builder
- Story 9.5: The fourth exemplar business through the Builder
- Story 9.6: The generalisation report
- Story 9.7: One real business, end to end
- Story 9.8: Two or three operator conversations

## Requirements & Constraints

- **The thesis fails if:** engine leaks do not fall toward zero from business 1 to business 4; any business needs a resolution the model cannot express; or setup effort does not fall materially across the build sequence. **No numeric targets anywhere, by decision.** Acceptance is directional and shape-based. Never invent a threshold.
- **Leak taxonomy (three levels):**
  - *configuration*: the expected path, covering most cases.
  - *supported extension point*: a leaf behind a declared contract, e.g. identity verification, document intake, a derived figure, a validator or a scorer.
  - *custom implementation*: the exception, never the path.

  Custom code may be a leaf, never control flow. The level a need lands at is a recorded judgement.
- **Leak classification is graded before the evidence.** The rules exist before the fourth business. Each class has a test a second person could apply. Every log entry records its evidence and who judged it. Existing entries are reclassified under the rules. This addresses a known critique: the measurements are self-graded and confounded by the learning curve. Leak classification and resolution strain are engineering judgements recorded by a person. They are not computed from episode records.
- **Builder inputs are clean.** A Builder session receives only the business's material and the operator's answers. No hand-written specification from Epics 1–2 is an input, and no earlier Builder output for that business is either. Each session record lists every input. A test fails if a hand-written specification is among them. No vertical starter templates exist in V1 (an approved decision), so conversation plus material is the only path.
- **Each build passes the single validation gate**, and its burden and yield are recorded with it. Burden is wall-clock time to a passing suite plus the number of source artifacts. Yield is rules recovered by interview, contradictions surfaced and defects recorded. Burden and yield are always reported together. Effort is compared across the four in build order.
- **Gym specifics:** identity verification is an extension point. An account is never mutated on the strength of a sender address. The deliberate failure case "I'm pregnant, so I need six months" must **escalate, not refuse**. It records two specification defects: whether pregnancy counts as a medical freeze, and whether the three-month cap can be waived.
- **The report states:**
  - whether leaks fell toward zero;
  - whether any business could not be expressed;
  - whether effort fell;
  - the **validity floor**: the share of episodes needing obligations, rules or action rather than plain information. A floor near zero means the demonstration proves nothing.
  - the **cost slope** in episodes per business, measured at the size reached. Episode volume per business is the dimension that grows; availability and scale are not V1 concerns.
- **O4 (resolution-kind enumeration) and O5 (faithfulness threshold) stay open.** The report presents evidence and options, and the user decides both.
- **Usefulness:** real inbound requests. Agent failures are reported separately from blocks caused by the business's own rules or capacity. The other three businesses may use authored corpora drawn from public enquiries, reviews and FAQs, and those results are labelled as such.
- **Operator conversation notes** record how the operator describes their rules, where printed and practised policy differ, and their answer to "how would you know the Agent did a bad job?"
- **Standing criteria:** `python -m pytest studio/tests -q` and `python -m studio scenarios` pass. Legacy suites stay green. No live model call is made without the user's approval. Every new Core check has an injection test and a mutation proof.

## Technical Decisions

- **Litmus test:** a new business is onboarded without a business-specific execution graph or state machine. A Core change made to fit a business is a leak and must be logged, not quietly absorbed. Business configuration never changes Core semantics. A genuinely new semantic capability is platform work, done once in the Core.
- **Dependencies point inward.** Extensions and adapters depend on Core contracts. External systems are reached only as Core contract → adapter → extension. No vendor name, branch or key appears in Core or Agent code. Model access goes only through an env-configured OpenAI-compatible `/v1`.
- **Resolution envelope is fixed:** goal, served or not, authority, evidence, business payload. The kind enumeration is deferred and should emerge from these runs.
- **The engine-leak log already exists** (started in Epic 1, kept in `docs/next-phase-proposals/PROOF-GATE.md` or its successor). Its first entry, brewery as business 2, was zero Core changes. One retroactive legacy entry exists, about the strict-consent change.
- **Build order of the four exemplars is a technical choice not yet made.** It is recorded in the decision register when chosen.
- **Credential-free deterministic mode** must keep working, so builds and the report can run with zero tokens. Live runs need approval each time.

## Cross-Story Dependencies

- 9.1 depends only on the existing leak log, so it can start now. 9.2 needs Epics 5–6 (the Builder, its burden/yield instrumentation, the workspace) plus 9.1. Then 9.2 → 9.3 → 9.4 → 9.5 run strictly in sequence, because effort is compared in build order.
- 9.6 needs 9.2–9.5 plus evaluation from records (Story 4.1) and faithfulness measurement (Story 4.6).
- 9.7 needs Epics 1–8 (including email go-live) and 9.1. It is **blocked on gate D13**: a real business, its operator, material and inbound mail.
- 9.8 is a human track owned by the user and can start now. It is **blocked on D13** (the user's time and contacts). Its notes feed Stories 5.3 and 5.7 and are recommended before 5.3.
- Gates D7–D15 and other PROPOSED/OPEN items are not decided. Nothing in this epic presumes their outcome.
