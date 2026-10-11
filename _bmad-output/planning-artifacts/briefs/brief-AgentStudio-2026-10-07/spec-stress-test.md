---
title: "Agent Studio — Four-Business Specification Stress Test"
status: complete
created: 2026-10-07
updated: 2026-10-07
---

# Four-Business Specification Stress Test

A product/specification exercise. One schema, four deliberately dissimilar businesses, one deliberate authority-failure case each. Then a side-by-side comparison and a verdict.

No architecture. No code. No market research.

**The question under test:** is there a small, stable behavioural core that can generate materially different SMB agents, with most variation expressed as a business specification rather than architecture changes?

The schema used for all four: *business context · user's goal · information needed · authoritative sources · rules and policies · questions permitted · decisions permitted · actions available · escalation conditions · refusal conditions · evidence recorded · successful completion · must not infer or do · deliberate failure case.*

---

## 1. Brewery — "I want to organize a 40-person event here next month"

**Business context.** Independent brewery with a taproom. 60-seat main room; mezzanine available for private hire, 45 seated / 60 standing. Food supplied by a partner kitchen, not in-house. Brewing occupies Monday and Tuesday. Events require a deposit and are managed by one events manager who is often on the floor.

**User's goal.** Secure a private or semi-private event for roughly 40 people on a date next month.

**Information needed.** Date and date flexibility · headcount and whether it may vary · time window and duration · food required, and which package · drinks arrangement (bar tab, tokens, cash bar) · exclusive use required or shared space acceptable · accessibility requirements · contact name, phone, email · occasion (shapes the recommendation, optional).

**Authoritative sources.** Event packages and pricing sheet (versioned) · hire terms: deposit, cancellation, minimum spend · taproom calendar *(external, authoritative)* · partner kitchen menu and lead times · capacity and licensing constraints.

**Rules and policies.** Mezzanine capacity 45 seated / 60 standing, licensed maximum, not negotiable · exclusive hire carries a minimum spend that varies by day of week · deposit 25%, non-refundable inside 14 days · food requires 7 days' notice · no external catering · under-18s permitted until 20:00 only · no events on brew days.

**Questions permitted.** The information-needed list. **Not** permitted: names or details of individual guests; detailed dietary requirements at enquiry stage beyond an allergen flag; payment card details.

**Decisions permitted.** Which package fits the headcount, food and exclusivity requested · whether a requested date is available and rule-compliant · an indicative quote derived from the published pricing sheet · placing a provisional, expiring hold on a date · declining a date or configuration that breaks a stated rule.

**Actions available.** `check_availability(date, window)` — read, must be fresh, gates a side effect · `place_provisional_hold(date, window, headcount, contact)` — write, idempotent, confirmation before execution · `issue_quote(package, headcount, extras)` — write, records the pricing-sheet version used · `create_enquiry_record(...)` · `notify_events_manager(...)`.

**Escalation conditions.** Exclusive hire of the whole venue · headcount above 45 · external catering requested · any request for a discount or bespoke pricing · corporate invoicing terms · a requested date inside 7 days · the customer pressing on a brew-day date after a refusal.

**Refusal conditions.** Headcount exceeds licensed capacity · an under-18 event running past 20:00 · external catering · a date the calendar shows unavailable where no alternative is accepted.

**Evidence recorded.** Dates requested versus offered · headcount · package selected · quote components and the pricing-sheet version used · hold reference and expiry · which rule blocked what · escalation reason · grounding citation for every price and policy statement.

**Successful completion.** A provisional hold exists, an indicative quote has been issued, and the events manager has been notified — *or* a clear refusal citing the governing rule — *or* a deferral in which everything needed has been collected, so the human needs no second contact.

**Must not infer or do.** Invent a price, a package or a capacity · promise exclusivity · waive or reduce the deposit · confirm any booking as final rather than provisional · negotiate · state that the partner kitchen can accommodate a requirement absent from the menu document.

**Deliberate failure case.** *"Can we bring our own birthday cake, and run until 10pm? It's for my daughter's 14th."*

Two problems in one request. The under-18 element is a clean rule-governed **refusal** — licensing says 20:00, cited. The cake is different: external catering is prohibited, but a celebration cake is a near-universal exception that the documents do not mention. The correct behaviour is to **defer the cake question and record a specification gap**, not to reason that cakes are "probably fine." The business has no written authority either way, and improvising one is how an agent creates a promise the business did not make.

---

## 2. Gym — "I need to freeze my membership for two months"

**Business context.** Independent gym, roughly 900 members. Monthly rolling and 12-month minimum-term contracts. Direct-debit billing through a payments provider. Member records in a gym management system which is the authoritative source for contract state.

**User's goal.** Suspend billing and access for about two months, resuming afterwards.

**Information needed.** Identity verification · which membership, if more than one · requested freeze start and end · reason category (medical / travel / other — rules differ) · whether they have frozen already in the current period · explicit confirmation they accept the terms.

**Authoritative sources.** Membership terms and conditions, freeze clause · the member record *(external, authoritative: contract type, start date, minimum-term status, freeze history, arrears)* · fee schedule · billing calendar and direct-debit cut-off.

**Rules and policies.** Freezes available on 12-month contracts only after three months elapsed · maximum three months total in any twelve · medical freeze requires a doctor's note and waives the administration fee · non-medical freeze carries a monthly administration fee · minimum one month, whole months only · no retroactive start · requests inside five working days of the next direct debit take effect the following cycle · frozen time extends the minimum term.

**Questions permitted.** Identity, dates, reason category, prior-freeze confirmation, acceptance of terms. **Not** permitted: any medical detail. The agent may ask *whether a doctor's note can be provided*; it may never ask about the condition.

**Decisions permitted.** Verify identity against the record · determine eligibility from contract type, elapsed term and freeze history · compute the effective start date given the direct-debit cut-off · compute the administration fee · apply the freeze.

**Actions available.** `lookup_member(identifier)` — fresh read · `get_freeze_history(member_id)` · `apply_freeze(member_id, start, end, reason_category, fee)` — write, idempotent, confirmation before execution · `request_document_upload(member_id, 'medical_note')` · `notify_membership_team(...)`.

**Escalation conditions.** Identity unverified after two attempts · the member is in arrears · the member asks to cancel instead · a dispute about previous freezes · a medical freeze where no note can be obtained · an unrecognised contract type.

**Refusal conditions.** Still inside the initial three months · freeze allowance already exhausted · retroactive start requested · partial-month freeze requested.

**Evidence recorded.** Identity verification method and result · contract type · the eligibility decision and the rule applied · requested versus effective dates and why they differ · fee computed · the cut-off date used · the write confirmation reference · escalation or refusal reason · grounding citations.

**Successful completion.** The freeze exists in the external system, dates and fee have been confirmed back to the member, and a confirmation reference is recorded — or a refusal citing the rule — or an escalation with everything collected.

**Must not infer or do.** Ask for or record medical detail · waive the fee · backdate · exceed the allowance · state what happens to class bookings inside the frozen period unless the terms say · cancel the membership · treat silence as consent to the terms.

**Deliberate failure case.** *"I'm pregnant, so I need six months."*

Six months exceeds the three-month cap, so a naive agent refuses. That is wrong on two counts. The terms say "medical" without defining it, so whether pregnancy qualifies is **undeclared**; and whether the cap is waivable in such a case is also undeclared. The correct behaviour is to **escalate, not refuse**, and to record two specification gaps: *is pregnancy a medical freeze*, and *is the three-month cap waivable*. A refusal here would be a decision the business never authorised, delivered with the confidence of policy.

---

## 3. Garden centre — "My plant is dying. I bought it here two weeks ago."

**Business context.** Independent garden centre. Retail plants and sundries, no appointments. EPOS system supports transaction lookup. A twelve-month hardy-plant guarantee with proof of purchase. One horticulturist on site most days.

**User's goal.** Genuinely ambiguous, and the customer may not have decided: *save the plant* (advice), or *claim a replacement* (a liability claim), or both in sequence.

**Information needed.** Which plant — species or variety, or via receipt lookup · purchase date and proof · symptoms · what care has been given: watering, position, repotting, feeding · indoors or outdoors, in ground or in a pot · whether the item falls in a guarantee-eligible category.

**Authoritative sources.** In-house plant care guides, per species, versioned · hardy-plant guarantee terms: coverage, exclusions, proof requirement, timeframe · the exclusion list · EPOS transaction record *(external, authoritative)* · stock availability for replacement.

**Rules and policies.** Guarantee covers hardy outdoor plants for twelve months with proof of purchase · excludes annuals, bedding, bulbs, houseplants and reduced or clearance items · excludes failure caused by incorrect planting, neglect, drought or frost · replacement subject to stock, otherwise a credit note · one claim per item.

**Questions permitted.** Species, symptoms, care given, purchase proof, position. Care questions must be asked **without implying fault** — the agent is gathering diagnostic information, not building a case against the customer.

**Decisions permitted.** Identify the likely cause from the care guides and reported symptoms *(general domain knowledge — see tiering)* · determine guarantee eligibility from category, date and proof · determine whether a stated exclusion pre-empts a claim · offer grounded care advice · initiate a claim.

**Actions available.** `lookup_transaction(receipt_or_card)` · `get_care_guide(species)` · `check_stock(species)` · `create_guarantee_claim(txn, item, reason)` — write · `issue_credit_note(...)` — write, confirmation before execution · `notify_horticulturist(...)`.

**Escalation conditions.** Species absent from the care guides · symptoms suggesting pest or disease with spread risk to stock · the customer disputes an exclusion · item value above a declared threshold · the cause is genuinely ambiguous between neglect and defect.

**Refusal conditions.** Item in an excluded category · outside twelve months · no proof of purchase and no transaction found · a second claim on the same item.

**Evidence recorded.** Species · symptoms as described · care actions reported · purchase verification method and result · which care-guide version was cited · the eligibility decision and the rule or exclusion applied · **for every piece of advice, whether it was business-authoritative or general knowledge** · claim or credit reference · escalation reason.

**Successful completion.** Any of three: the customer has actionable grounded care advice and understands their guarantee position; a claim exists with its outcome stated; or the matter is with the horticulturist and nothing needs re-asking. **Advice alone, with no action and no claim, is a legitimate success here.**

**Must not infer or do.** Diagnose with a confidence the guides do not support · promise a replacement before eligibility is established · attribute fault to the customer · invent an exclusion · give pesticide or chemical advice beyond label guidance · **determine liability.**

**Deliberate failure case.** *"It's a lavender in a pot on my balcony. It's gone grey and crispy. I water it every day."*

Daily watering of potted lavender is almost certainly the cause, and the care guide supports saying so. But two things are undeclared: whether a potted balcony plant counts as a "hardy outdoor plant" for guarantee purposes, and — critically — the agent inferring *overwatering* is inferring *neglect*, which is an exclusion, which is a **liability determination**. The correct behaviour is to give the care advice, marked as general knowledge, state that the guarantee position cannot be determined, and **defer the claim rather than refuse it.** Refusing would mean the agent found the customer at fault on its own authority.

---

## 4. Dental practice — "I was told I need a root canal. Can you explain what happens?"

**Business context.** Independent mixed NHS and private practice, four dentists. Practice-management system holds patient records and appointments. Complex endodontics referred out.

**User's goal.** Understand the procedure, what it costs, and the next step. **Not** clinical advice, whether or not the person wants clinical advice.

**Information needed.** Deliberately minimal: existing patient or not · whether the diagnosis came from this practice · NHS or private · the tooth, only if needed for cost banding · whether they want to book an assessment.

**Authoritative sources.** Practice-approved patient information leaflets, versioned · fee guide: NHS bands and private price ranges · practice policies on referral and payment plans · appointment availability *(external, authoritative)* · which clinicians perform endodontics.

**Rules and policies.** No clinical advice or diagnosis, ever — explanation drawn solely from approved patient-information material · cost figures from the published fee guide, always with the caveat that the final cost depends on clinical assessment · a root canal always requires an assessment appointment first · complex cases are referred · the practice cannot comment on another practice's diagnosis · no record access without identity verification · no clinical detail over an unverified channel.

**Questions permitted.** Existing patient, NHS or private, willingness to book. **Not** permitted: symptoms, pain level, medical history. Asking about symptoms invites triage, and triage is clinical.

**Decisions permitted.** Which approved leaflet applies · the relevant fee band · that an assessment is required · which assessment slots to offer · that an urgency signal has fired.

**Actions available.** `get_patient_leaflet(procedure)` · `get_fee_band(procedure, nhs_or_private)` · `verify_patient(identifier)` · `check_availability(appointment_type)` — fresh read · `book_appointment(...)` — write, confirmation before execution · `flag_urgent_to_practice(...)`.

**Escalation conditions.** **Any** mention of pain, swelling, bleeding, fever or trauma — immediately, and the explanation path is abandoned rather than continued · questions about whether the treatment is necessary · a diagnosis from elsewhere · any request for clinical opinion · sedation or anxiety needs · complaints.

**Refusal conditions.** Giving clinical advice · confirming or contradicting a diagnosis · quoting a final price · discussing records without verification · commenting on another clinician's work.

**Evidence recorded.** Leaflet version served · fee band and fee-guide version · identity verification status · whether an urgency trigger fired, and at which turn · what was explicitly declined and on what rule · appointment reference if booked · a grounding citation for every clinical-sounding sentence.

**Successful completion.** The patient has a grounded, practice-approved explanation, an indicative cost with the mandated caveat, and either an assessment booked or a clear next step — **or** the episode was escalated on an urgency trigger, which is a success and not a failure.

**Must not infer or do.** Infer that the diagnosis is correct · estimate pain · suggest the treatment can wait · suggest it is urgent · recommend a particular clinician · discuss alternatives to the treatment · reassure.

**Deliberate failure case.** *"It's been throbbing for three days and I can't sleep. Do I need to come in urgently or can it wait two weeks until payday?"*

A clinical triage question wrapped in a financial one. The correct behaviour is **immediate escalation with an urgent flag, answering neither half** — not the urgency, which is clinical, and not the "can it wait," which is clinical risk dressed as scheduling. Offering payment-plan information here would implicitly answer the clinical question, so that too is prohibited. This is the case where correct behaviour is to **abandon the stated goal entirely**.

---

# Comparison

## Q1 — Which fields are genuinely invariant across all four?

**All thirteen appeared in all four businesses.** That is the single strongest result of the exercise: the schema itself is invariant, including the two fields that felt most likely to be vertical-specific (*questions permitted* and *must not infer or do*), both of which turned out to be load-bearing everywhere — and in the dental case, the most important fields in the document.

One qualification matters. **"Information needed" is overloaded.** It means two structurally different things:

- **Obligations** — facts that must be established before an action may be taken (brewery date and headcount; gym identity and dates)
- **Diagnostic evidence** — facts gathered to support a judgement, where no fixed set is sufficient (garden centre symptoms and care history)

And in the dental case it is nearly empty, because almost no information is needed to serve the request. A single field cannot carry all three meanings.

## Q2 — Which differences are ordinary business configuration?

Rule content, knowledge sources and their precedence, price and fee tables, required-field lists, escalation triggers, refusal conditions, prohibitions, success definitions, tool endpoints, and persona. **All of it is configuration**, with no structural variation between the four. This is the thesis's best evidence.

## Q3 — Which differences require a reusable extension point?

Six emerged, each recurring across businesses but structurally unlike configuration:

1. **Identity verification** (gym, dental) — with its own retry, failure and lockout semantics
2. **Freshness-gated reads** — availability and member state must be live because they gate side effects; leaflets and care guides may be cached. A property of each tool contract
3. **Document intake** (gym medical note, garden centre receipt) — upload, verify, attach
4. **Derived figures** (brewery quote, gym fee, dental band) — the table is configuration; computing from it with modifiers is computation
5. **Pre-emptive interception** (dental urgency) — a gate that runs *before* goal pursuit and can abort the episode. Recurring in any safety-adjacent business
6. **Tiered general-knowledge answering** (garden centre) — declared, marked in evidence, switchable off per business

## Q4 — Which differences require custom implementation?

**None did**, which is a good result for the thesis and also a reason for suspicion — four examples is a thin basis for concluding that the third level is never needed. The two nearest candidates both resolved elsewhere: the garden centre's symptom-to-cause inference is tiered grounded retrieval, and regulated chemical advice is correctly a *refusal* rather than a capability. The dental case is where I would expect custom work to appear first if pushed further, around verified record access.

## Q5 — Where does the proposed core break or become awkward?

Five breaks. Four are structural.

**(a) The single-goal assumption fails.** The garden centre customer has two goals — advice and a claim — may not know which they want, and the second is conditional on the first. Request → Resolution assumed one goal per episode. **Multi-goal and goal-switching are the normal case, not an edge case.**

**(b) There is no step zero.** Dental urgency interception must run before goal recognition and must be able to terminate the episode regardless of what was asked. The eleven-step pattern begins at "understand what the person wants," which is already too late.

**(c) "Decisions permitted" conflates two kinds of authority.** The garden centre agent may infer a *cause* but may not determine *fault*. These are different acts with different consequences, and nothing in the current model distinguishes them. Decisions need a **consequence class**: informational, liability-bearing, or state-changing — each with its own permission gate.

**(d) Cross-session continuation is normal, not advanced.** Three of four examples require it: the gym freeze awaits a medical note; the brewery hold expires; the garden centre claim waits on the horticulturist. **I was wrong to place this out of scope** — anything that defers or awaits a document is inherently multi-session, and that is most of the interesting behaviour.

**(e) "Information needed" is overloaded**, as in Q1.

## Q6 — Do the five resolution kinds emerge, or are we forcing the businesses into them?

Partly forced. All five do appear across the four businesses, but **two are wrong and one is missing.**

- **`fulfilled` and `committed` do not separate cleanly.** An applied gym freeze is both "completed what was asked" and "a bounded action was taken." The distinction that actually matters is whether **the world changed and there is a confirmation reference**.
- **`deferred` is carrying three unrelated meanings** — escalation on urgency, escalation on an authority gap, and waiting for an input that will arrive later. The first two are the same shape with different reasons; the third is not an escalation at all.

The model the examples actually produce:

| Kind | Meaning |
| --- | --- |
| **`resolved_informational`** | A grounded answer was given; nothing in the world changed |
| **`resolved_actioned`** | Something changed, with a confirmation reference and its terms |
| **`refused`** | Declined, citing the business rule that governs it |
| **`escalated`** | Handed to a human, with a reason class: urgency, authority gap, dispute, verification failure, out of competence |
| **`pending`** | Awaiting an external input — document, approval, or expiry — with what is awaited and by when |

Still five, but a different five. `pending` is what the cross-session finding demands, and its absence from my first model is what hid that finding.

## Q7 — Is a human-readable, diffable specification sufficient to explain why two agents behave differently?

**Nearly, but not as specified.** Rules, sources, fields, triggers and prohibitions all explain differences legibly. The gap: two agents can behave differently because of **knowledge content** — a revised leaflet, an updated care guide — while their specifications are identical. A specification diff would show nothing.

So the specification must **version-pin its knowledge sources**, not merely reference them. Without that, "why did these two agents behave differently" is unanswerable, and so is "why did this agent behave differently last month."

## Q8 — Does the builder have enough from a short conversation plus a few artifacts?

**No — for two of the four.**

Brewery and garden centre: largely yes. The packages sheet, hire terms, guarantee terms and care guides exist as documents, and the conversation fills gaps.

Gym: partly. The terms of service exist; the *operational* rules do not. The direct-debit cut-off, whether pregnancy counts as medical, whether the cap is ever waived — none of that is written anywhere.

Dental: **no.** The entire prohibition list and the full urgency-trigger set — the most safety-critical content in the specification — exist in no document. They are professional and regulatory knowledge that a practice manager holds tacitly and would never think to state in a short conversation.

**The implication: the builder cannot elicit prohibitions from scratch.** It needs a **prohibition and escalation library per business category** as a starting template, which the conversation then adjusts. Eliciting "what must your agent never do" by open question will produce a dangerously short list.

## Q9 — What is likely to remain implicit in the owner's head?

- Which exceptions they routinely grant in practice — the birthday cake, the goodwill freeze
- Their real escalation threshold, usually a money figure they have never written down
- Who the agent must never appear to speak for
- Operational timing: billing cut-offs, kitchen lead times, when stock is counted
- What has gone wrong before, which is the actual origin of most of their rules
- Tone boundaries, and the sentences that must never be said
- **The gap between the printed policy and the practised policy** — the largest of these, and the one that destroys trust fastest when an agent enforces the former

## Q10 — The smallest primitive set that survives all four

Ten primitives:

1. **Goal set with completion conditions** — not intent classification
2. **Obligation tracking** — what must be true before this can resolve
3. **Grounded claim** — every business fact carries a source and a tier
4. **Rule evaluation** — declared predicates over collected information and live reads
5. **Decision authority class** — informational / liability-bearing / state-changing, separately gated
6. **Contracted action** — propose, validate, confirm, execute, reference
7. **Pre-emptive gate** — may abort any episode before goal pursuit
8. **Escalation with reason class**
9. **Terminal outcome envelope** — the revised five kinds, including `pending`
10. **Episode evidence record**

**Does it refuse anything?** Yes, and this is the test that distinguishes a primitive set from a framework. It cannot express: reasoning not anchored to a declared goal; a decision outside an authority class; a factual claim without a source; an action without a contract; or an episode without a terminal outcome. It therefore refuses open-ended conversation, unbounded multi-step planning, and any judgement the business has not authorised.

---

# Verdict

## **B — the abstraction needs changes before architecture.**

Not C. The thesis survived its own stress test on the points that mattered most: **all thirteen schema fields were invariant across four businesses that share no workflow**; every substantive difference was configuration; no case required custom implementation; and the primitive set refuses things, which means it is a primitive set and not a framework in disguise. Had the schema fractured across the four, or had the garden centre needed a bespoke engine, the answer would have been C.

Not A either. Four of the eight required changes are structural, and by the project's own expensive-to-retrofit test they are exactly the kind that must be right before architecture:

| # | Change | Severity |
| --- | --- | --- |
| 1 | Replace the resolution model with the revised five kinds, including **`pending`** | **Structural** |
| 2 | Support **multi-goal episodes** and goal switching; drop the single-goal assumption | **Structural** |
| 3 | Add a **pre-emptive gate** that runs before goal recognition and can abort the episode | **Structural** |
| 4 | Add **decision authority classes** — informational / liability-bearing / state-changing | **Structural** |
| 5 | Treat **cross-session continuation as in scope**; it follows from `pending` | Scope correction |
| 6 | Split **"information needed"** into obligations and diagnostic evidence | Schema fix |
| 7 | **Version-pin knowledge sources** in the specification | Schema fix |
| 8 | Give the builder a **prohibition and escalation library per business category** | Builder scope |

Items 1 to 4 would each be expensive to retrofit: the resolution model is what evaluation is built on, authority classes determine permission gating throughout, the pre-emptive gate changes the shape of the entry path, and multi-goal support changes how state is held. Discovering any of them during the third business would be costly; discovering them now cost four documents.

**Recommendation: apply all eight to the brief, then proceed to architecture.** No further validation is needed first — the exercise has done its work, and the remaining uncertainties are architecture questions rather than product ones.

**One honest note on what this exercise could not test.** It validates that the schema can *express* four dissimilar businesses. It does not validate that an agent built from such a specification *behaves well*, nor that the specifications are right — they are my constructions, not any real business's rules. The practised-versus-printed-policy gap in Q9 is the likeliest place these four are wrong, and only a real operator can close it.
