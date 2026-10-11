# Brief Extract for UX Specification — Agent Studio

Sources read in full:
- `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/brief.md` (258 lines, status: final)
- `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/addendum.md` (859 lines, status: compiled)

Source read for fragility/contest flags only:
- `_bmad-output/planning-artifacts/briefs/brief-AgentStudio-2026-10-07/spec-stress-test.md` (291 lines)

Section references are to the headings of each file. `[INFERRED]` marks anything not stated.

---

## 0. HEADLINE WARNING FOR THE UX WORKFLOW — read before anything else

**The brief is an architecture-and-market-evidence document, not a positioning-and-voice document.** The task framing assumed "the brief is where POSITIONING and VOICE live." For this brief that is only half true: positioning-against-category is strong and quotable; **brand voice, tone adjectives, taglines, naming, operator-facing vocabulary, personas and any UI opinion are essentially absent.** Items 1, 4, 8, 11 below are mostly BRIEF SILENT. The UX spec will be *originating* the voice layer, not transcribing it.

**Three places the UX task brief diverges from what the documents actually say — flag these to the user:**

1. **"V1 channel is email / inbound messaging" is NOT in the brief.** The brief leaves the channel *open*: brief §Open Architecture Questions lists "**Retrieval architecture, model strategy, the V1 channel**" as undecided, with "Grounding, tiering and channel-independence are requirements; the implementations are not decided." Scope says only: "**Voice — a separate, already-proven project. Channel is an adapter; one channel ships for V1 and the core never learns which it is on**" (brief §Scope). Channel-count ("one channel ships for V1") and voice-exclusion are decided; **email is not named anywhere in either document as the V1 channel.** Email appears only as market data (addendum §1.4: "US contact preference: text 33%, **email 28%**, web chat 21%, phone 18%"; §1.6 Clio "phone + email + website chat").
2. **"Text-first" was REOPENED, not settled.** Addendum §5.4: "**text-first vs voice was reopened** as a DECIDED item, on the grounds that it may have been architecture-driven rather than product-driven. It was **not automatically reversed**." *Inbound* (vs outbound) remained decided throughout.
3. **The brief never calls the operator-facing product a "Builder" conversation with a "smart onboarding."** It calls it "The Builder's Role," scoped "deliberately minimal," and the word "onboarding" appears in the brief only in the OUT list ("onboarding automation"). See §8 below.

---

## 1. WHO THE OPERATOR IS

**Named persona: BRIEF SILENT.** No persona, no name, no demographic, no day-in-the-life, no sophistication or technical-comfort assessment anywhere in brief.md or addendum.md.

What *is* said, verbatim:

- "Agent Studio is a reusable behavioural agent system for **small businesses**." (brief §Executive Summary)
- The business types, verbatim: "**A brewery on Tuesday, a dental practice on Saturday, a gym and a garden centre the week after**" (brief §Executive Summary).
- Business sizes, only from spec-stress-test business contexts (used here as the only sizing signal available): brewery = "Independent brewery with a taproom… events are managed by **one events manager who is often on the floor**"; gym = "Independent gym, **roughly 900 members**"; garden centre = "Independent garden centre… **One horticulturist on site most days**"; dental = "Independent mixed NHS and private practice, **four dentists**."
- The knowledge lives partly nowhere but in the operator: "the knowledge needed to answer them well already exists — in a price list, a policy, a care guide, a membership agreement, **the owner's head**." (brief §The Problem)
- The operator is the holder of tacit rules: "Which exceptions they routinely grant in practice… Their real escalation threshold, **usually a money figure they have never written down**… Operational timing: billing cut-offs, kitchen lead times, when stock is counted… What has gone wrong before, which is **the actual origin of most of their rules**… Tone boundaries, and the sentences that must never be said." (spec-stress-test §Q9 — treat as diagnostic, not decided)
- **The operator has never been met.** "no primary operator evidence was obtainable. **Two or three conversations with real small-business operators remain the only test of the problem statement**" (brief §Market Honesty). Addendum §1.9: "**Reddit was blocked to the researcher**, so **no primary operator-voice corpus was obtainable at all.**"

**What they are doing instead (the current coping strategies), verbatim** (brief §The Problem):
> "A person answers when they can and misses the rest, concentrating failure after hours and at peak. A web form captures a fraction of what is needed and begins a round of clarifying messages. A scripted chatbot deflects to a link. An answering service takes a message but cannot apply the business's rules. A document-retrieval chatbot answers questions but cannot *do* anything, so every request needing an action still reaches a person."

Priced alternatives they are paying for today (addendum §1.3): "answering services **$100–400/mo** (overage **$0.75–1.50/min**); virtual receptionists **$165–2100/mo**"; Smith.ai human-first "**$300/30 up to $2100/300 ($7–10 per call)**"; Ruby "**$250/50min to $1725/500min**."

`[INFERRED]` Operator technical comfort: non-technical. The brief never says so, but it requires "The specification must be a **first-class, human-readable, diffable artifact**" with "Human review stays in the loop" (brief §The Builder's Role) while giving the operator no code surface at all — and the whole three-level variation contract exists so that normal variation is "configuration / specification," never code.

---

## 2. THE PAIN

**Operator's own words: BRIEF SILENT.** There are no operator quotes in either document; §1.9 of the addendum explains why (no obtainable corpus, contaminated public record).

The pain as stated, verbatim (brief §The Problem):
> "Small businesses answer the same requests endlessly, and the knowledge needed to answer them well already exists… What does not exist is anything that can hold the conversation and act on that material."

> "The underlying problem: **a small business's rules and knowledge are not in a form anything can act on**, so every inbound request consumes human attention from scratch."

Where failure concentrates: "**after hours and at peak**" (brief §The Problem).

**Cost of a missed or badly handled request:** the brief refuses to put a number on it.
- "**Unusable — vendor marketing.** 411 Locals '37.8% answered'; AMBS '**$126k/yr lost**'. Both are vendor-published category stats with no independent basis and **must not be cited**." (addendum §1.3)
- "Most defensible independent-ish figure: **CallRail, Jan-2025, over 1.1M leads** — missed-call rates **32% healthcare, 28% legal, 14% home services, 9% real estate**… this is *far below the 62% the category sells on*, i.e. the industry's headline missed-call number is **inflated by roughly a factor of two** against the best available data." (addendum §1.3)
- "**No independent per-vertical appointment-value dataset was found.** Any per-booking value used downstream is therefore an assumption, not a finding." (addendum §1.3)
- No-shows: "**~23% meta across 105 studies**; dental **15–20%**, vet **10–12%**." (addendum §1.3)

**UX consequence `[INFERRED]`:** the product may not display or market any "£X lost to missed calls" style figure. The brief has explicitly disqualified every available number of that shape, including by naming the fabrication mechanism (addendum §1.9).

**The worst pain named, which is a trust pain not a volume pain:** "**The gap between the printed policy and the practised policy** — the largest of these, and the one that **destroys trust fastest when an agent enforces the former**." (spec-stress-test §Q9)

---

## 3. POSITIONING AND CATEGORY

### What it IS (verbatim)
- "a **reusable behavioural agent system** for small businesses" (brief §Executive Summary)
- "**The product is the machinery, not any one agent.**" (brief §Executive Summary)
- The one-line operating description: "Given a short conversation about a business and a few of its own documents, it produces a versioned specification, validates it, and deploys an agent that handles that business's inbound requests."
- The behaviour description, which is the best available "what it is" sentence for UX purposes (brief §Executive Summary):
  > "The agent works out what the person is trying to accomplish, obtains what it still needs, grounds every business fact in the business's own material, concludes only what the business has authorised, acts only through declared contracts, escalates what it may not decide, and closes with a structured outcome it can be judged on."
- The discriminating sentence (brief §What Makes This Not an FAQ or RAG Chatbot): "The discriminator is **obligation**. This agent knows what must be true before a request can resolve, and will not resolve it until those obligations are met or explicitly waived."
- Four verbatim capability claims against the category (same section):
  1. "**Hold an unfinished request open** — across turns, and across sessions — driving toward what is missing"
  2. "**Refuse with a reason** drawn from the business's own rules, rather than failing to find an answer"
  3. "**Change something in the world** through a bounded, contracted, verified action"
  4. "**Close with a structured resolution** that can be evaluated, counted and audited"
- "And the quality bar that is not a feature: **never state a fact about the business that does not come from the business's own version-pinned material.**"

### What it explicitly IS NOT (verbatim, brief §Scope "Out, explicitly")
- "**Any vertical framing. Not a booking, appointment, healthcare, sales or FAQ product**"
- "Platform-initiated outbound conversation… **it never independently starts an outbound conversation or episode**"
- "**Owning any system of record.** External business systems stay authoritative"
- "**Agent-generated planning or goal decomposition**"
- "**Long-term customer memory, cross-episode profiling, proactive outreach**"
- "**Continuous automatic learning.** Behaviour changes are reviewed and promoted, never silently mutated"
- Elsewhere: "The purpose is conversational robustness, not autonomous planning. **This is not a workflow engine.**" (brief §Multi-goal, deliberately bounded)
- "A document chatbot has no obligations, no authority model, no completion condition and no outcome." (brief §What Makes This Not an FAQ or RAG Chatbot)
- Rejected by hard user condition: "'**An AI receptionist that books appointments**' — **Rejected by hard condition**, user-stated: commoditised, and existing competitors must **not** become an excuse for building a worse copy. **Not an acceptable thesis**" (addendum §5.1)
- "**becoming a workflow platform was explicitly refused**" (addendum §3.4 empty-cells table)

### Competitors named, and what we do differently
Named incumbents (brief §Market Honesty; addendum §1.1, §1.5, §1.6, §2):
TrueLark (acquired by **Weave, NYSE:WEAV, $35M**, closed 2025-05-20, now "Weave AI Receptionist"), **ServiceTitan** Virtual Agent Inbound SMS, **Mindbody Messenger[ai]** (since the 2019 Bowtie acquisition, **$99–199/location/month**), **Zenoti**, **Podium AI Employee** ($399–599/mo), **Boulevard** (not shipped), **Jane App** (scribe/charting not booking), **Salesforce/Qualified (Piper, $1.2B, closed April 2026)**, **HubSpot Breeze (~$0.50/resolution)**, **Intercom Fin for Sales ($9.99 per qualified lead)**, **Agentforce (~$2/conversation)**, **Clio Grow AI (launched 2026-08-20, $25 per converted lead)**, **MyCase**, **NexHealth**, **Vetstoria**, **Fresha**, **Square Appointments**, **Smith.ai**, **Ruby**, **Swiss Monkey** (the fabrication source), **11x** (the discredited one).

**What the brief says we do differently — and it is deliberately NOT a moat claim:**
> "**No commercial moat is claimed.** This is a technically substantial system built against a real problem. Commercial potential is unproven and probably modest for a solo builder, and **the project is not justified by it.**" (brief §Market Honesty)

The structural reason third-party differentiation is hard, verbatim: "the system-of-record owner **controls the write API, owns distribution, holds the outcome data, and can price on outcome because it alone observes the outcome.**" (brief §Market Honesty)

**The single unoccupied differentiator found** (addendum §1.8): "(d) **counterfactual replay** — show how a rule change would have altered past conversations — **ABSENT from every vendor examined** — the only unoccupied cell." But: it "has value only when attached to a calendar with **live-capacity write access**" (addendum §2), and in V1 it is not in scope (brief §Scope does not list it).

**The trust-framed competitive insight — the most UX-load-bearing line in the addendum** (§1.7):
> "**Shipped-and-FENCED, not shipped-and-dark.** Both public vendors fence the agent to **overflow and after-hours by default** and expand 'incrementally'… ServiceTitan's CFO: *'many customers start with overflow and after hours… now we also have customers that opt to let VA handle incrementally more and more volume.'* INTERPRETATION recorded in the memlog: operators enable it in the window where a mistake costs least; **that fencing is a trust deficit expressed as configuration.**"

Also load-bearing for how we talk about quality (addendum §1.8):
> "**The real moat is not conversation quality or explainability — it is write access to the calendar with live capacity**… ServiceTitan reports a **70% booking rate including capacity constraints vs 90% excluding them** — the dominant failure is that *the calendar had nothing to offer*, a business-rules and capacity problem, **not comprehension**."

---

## 4. BRAND VOICE, TONE, VOCABULARY

### Stated adjectives, taglines, naming, voice guidance
**BRIEF SILENT.** There is no tone section, no adjective list, no tagline, no naming guidance, and no copy sample anywhere in brief.md or addendum.md. The target feeling in the UX task framing ("simple, calm, intelligent, trustworthy, business-oriented, conversational rather than technical") appears **nowhere** in these documents — it must be treated as the user's own input to the UX workflow, not as brief-derived.

### The one piece of voice guidance that exists — and it is about the *generated agent*, not the product UI
- Spec field: "**Identity** — what the business is, **how it speaks, what it will not say**" (brief §The Business-Specific Specification). So voice is **per-business configuration**, authored by the operator, not a product-wide tone.
- The elicitation gap on it: "**Tone boundaries, and the sentences that must never be said**" are named as likely-implicit in the owner's head (spec-stress-test §Q9).
- Also implicit: "**Who the agent must never appear to speak for**" (spec-stress-test §Q9).

### The product's central phrase, which is the only quotable brand line
> "**Reasoning is broad; authority is bounded.** The agent may think widely about a request. What it may *conclude*, and what it may *do*, are narrow and declared. That asymmetry is the product's central discipline." (brief §The Behavioural Chain)

### Vocabulary the brief uses INSTEAD of "agent / prompt / RAG / policy / model"

**Important honest finding:** the brief does NOT establish an operator-facing vocabulary. It establishes an *internal/architectural* vocabulary, and that vocabulary still contains words an operator must never meet. The table below maps the forbidden concept to the brief's term, and flags which brief terms are themselves too technical to surface.

| Forbidden concept | The brief's word for it (verbatim) | Surfaceable to the operator? |
|---|---|---|
| prompt | "**specification**" / "**business specification**" — explicitly not a prompt: "Seam 2 — Versioned specification (**not a generated prompt, not generated code**)" (addendum §3.2) | `[INFERRED]` Only as "Business Specification" — the UX task framing already adopts this. Note the brief also calls it "the agent definition" (addendum §3.3 C2) |
| RAG / retrieval / embeddings | "**grounding**", "**grounded claim**", "**authoritative sources**", "**the business's own material**", "**version-pinned sources**", "**knowledge sources**", "**precedence when they conflict**" | "your own material", "where this came from" are operator-safe `[INFERRED]`; "grounded claim" and "version-pinned" are not |
| policy | the brief uses the word "policy" freely — "**rules and policies**", "**escalation policy**", "policy violation", "policy compliance". Operator-nearer alternatives present in the brief: "**rules**" ("eligibility, pricing, timing, policy, constraints"), "**what this business will not let an agent decide**", "**what overrides the ordinary path**", "**what must be established before**" | "**rules**" yes. "policy" is borderline — it is ordinary business English, unlike the others `[INFERRED]` |
| model / LLM | the brief says "**the model**" and "LLM" throughout internally; the only operator-facing framing available is the two-tier split: "**Business-authoritative facts**" vs "**General domain knowledge** … **May come from the model, must be marked as such**" | No. `[INFERRED]` the operator-facing idea is "facts from your business" vs "general knowledge", with the latter being switchable: "**enabled or disabled per business as a declared risk**" |
| agent | the brief uses "**agent**" as its primary noun and offers no replacement. Adjacent nouns it does use: "**instance**", "**deployable instance**", "a **brain-only** project (voice project only)". Competitor framings recorded: "**AI Receptionist**", "**AI Employee**" (Podium), "**virtual receptionist**", "**virtual agent**" | **BRIEF SILENT on a replacement.** This is the single biggest vocabulary gap the UX spec must fill |
| episode / session | "**episode**" — "The unit is the episode, and it is resumable" | `[INFERRED]` not operator-safe; the operator words available in the brief are "**a request**", "**an inbound request**", "**a conversation**" |
| guard condition | "**Guard conditions** — what overrides the ordinary path", families: "**urgency, authorisation failure, policy violation, unsupported request, identity problem**" | `[INFERRED]` "what should stop everything else" |
| HITL / escalation | "**Escalation with reason class**", "**Handing to a human, with why**", "**what this business will not let an agent decide**" | "hand to a human", "what it must never decide" — operator-safe `[INFERRED]` |
| tool call / action | "**Contracted action** — Propose, validate against contract, confirm, execute, obtain evidence of success"; "**what it may do, against which system, under what contract, with what success evidence**" | "what it may do" yes; "contract" no `[INFERRED]` |
| eval | "**Evaluation criteria** — **what good looks like here**" | "what good looks like here" is the single best operator-facing phrase in the brief |
| state / outcome enum | "**Resolution record** — the business outcome"; "resolution families" candidates: "*served with information*, *served with action*, *declined under a declared rule*, *handed to a human*"; lifecycle: "**active, pending and resumable, or closed**" | The resolution family names are *written in plain English on purpose* and are the most operator-ready strings in the brief |

**Flag:** the resolution enum is **deliberately not final.** "Resolution families are deliberately **not fixed as a final enum** in this brief… the enumeration is an architecture decision, made once the runtime model is clear. **Candidate families, provisional**" (brief §Three orthogonal dimensions). The stress test's competing five — `resolved_informational | resolved_actioned | refused | escalated(reason class) | pending` — are named in the addendum (§5.6) as a prior revision, **not** as the final set. Do not hard-code either set into UI copy without flagging it as provisional.

---

## 5. TRUST — exhaustive

This is the richest seam in the documents and the brief is explicit that trust, not capability, is the gap.

### The thesis statement
> "**Reasoning is broad; authority is bounded.** … What it may *conclude*, and what it may *do*, are narrow and declared. That asymmetry is the product's central discipline, and **the verification link keeps it honest — an agent may never report that something happened without evidence that it did.**" (brief §The Behavioural Chain)

### The generic guardrail library — the five promises, verbatim (brief §The guardrail and authority library)
> "A **reusable library of generic behavioural constraints**, part of the core and applying to every agent:
> - Do not invent business facts
> - Do not act outside declared authority
> - Do not perform undeclared actions
> - Do not claim an action succeeded without evidence
> - Escalate when required authority or evidence is unavailable"

These five are the closest thing the brief has to a trust *promise set*, and they are written in plain imperative English. `[INFERRED]` They are near-ready as operator-facing copy.

### Three separately gated authority classes
> "**Decision authority classes** — Separately gated: information the agent may provide; conclusions it may draw under declared authority; state-changing actions" (brief §The Reusable Behavioural Core)

The insight that forced them, verbatim (addendum §5.8) — **the clearest single illustration of blast radius in the documents:**
> "**The sharpest new finding (garden centre): inferring a CAUSE and determining FAULT are different acts with different consequences.** The agent may say *'daily watering is almost certainly the problem'* (grounded care advice) but may **not** conclude *'therefore this is neglect, which is excluded, claim denied'* — that is a **liability determination made on its own authority**. **Nothing in the prior model distinguished them.**"

Stress-test naming of the three: "**informational, liability-bearing, or state-changing** — each with its own permission gate" (spec-stress-test §Q5c).

### Control and oversight mechanisms
- Confirmation gates: "**Contracted action** — Propose, validate against contract, confirm, execute, obtain evidence of success"; spec declares "**which require explicit confirmation**" (brief §The Behavioural Chain).
- Verification link: "What evidence proves an action succeeded, and **what happens when that evidence is absent**" (brief §The Behavioural Chain).
- "**An action record is evidence that something happened, not a resolution.**" (brief §Three orthogonal dimensions)
- Human in the loop on build: "**Human review stays in the loop.**" (brief §The Builder's Role)
- Reviewability as the diagnostic requirement: "**a bad agent has two possible causes — a bad specification or a bad core — and only a reviewable specification lets anyone tell which.**" (brief §The Builder's Role)
- No silent change: "**Continuous automatic learning** — Out… Behaviour changes are **reviewed and promoted, never silently mutated**" (brief §Scope). Addendum §3.1: behaviour changes are "**reviewable, promotable and revertable**".
- Promotion as a reviewed act: "these four have the shape of version control — spec = checked-in state, evidence = the working tree, promotion = **a pull request on behaviour**" (addendum §3.1). `[INFERRED]` the metaphor is a developer metaphor and must not reach the operator in those words.
- The four-artifact split (addendum §3.1): **Specification** (intended behaviour, "Changed only by deliberate, reviewed promotion"), **Evidence** (append-only), **Evaluation** (append-only, versioned per agent version), **Deliberate changes** ("Reviewable, revertable, attributable").
- The product's job restated, and this is a direct UX mandate (addendum §3.1):
  > "the product's job is **not to measure conversational quality objectively** (quality is irreducibly contested) but to make **disagreement cheap to express and fast to propagate**"
- Bounded automatic promotion deliberately refused: "Behaviour promotion — **Leave empty: automatic, threshold-automatic** — Silent learning was rejected. **Empty on purpose, documented**" (addendum §3.4).
- Fully agentic action deliberately refused: "Action selection — **Leave empty: fully agentic tool selection** — Incompatible with bounded actions and deterministic execution; **the cell that makes safety and evaluation both intractable**" (addendum §3.4).
- Execution is never the model's: "**The agent proposes, authoritative systems dispose**… The LLM decides *what it wants to do* and emits a structured action proposal; **it never controls execution.** Execution is deterministic, bounded, validated against a declared contract, and gated where consequences require it." (addendum §3.1 Principle 2)
- Agent owns no truth: "**external systems remain authoritative** (recorded as 'the most consequential inversion of the session')" (addendum §3.1).

### The operator's fear, as evidenced
- The fencing finding (addendum §1.7, quoted in full in §3 above): operators of competing products "**enable it in the window where a mistake costs least; that fencing is a trust deficit expressed as configuration.**"
- Approval-before-commit is already the market default: "(b) approval-before-commit — **Shipped as Weave's DEFAULT for most verticals**: 'let AI Receptionist capture appointment requests, **then let your team review and schedule**'" (addendum §1.8). Also: "**Weave's AI Receptionist books directly only into qualified dental PMSs, every other vertical is CAPTURE-ONLY**" (addendum §1.8).
- Consumer-side (not operator-side) acceptance, vendor-run and caveated: "**vendor-run survey (Zenoti's own): 55% of salon and 71% of medspa clients** comfortable with an AI receptionist — so **~45% of salon clients are not**." (addendum §1.3)
- Competitors already ship a supervision surface: "a supervision **Command Center** announced at Pantheon 2026: '**one way for your team to supervise all the agents, configure them, monitor their performance**'" (addendum §1.8).
- Per-conversation review and longitudinal quality are also already shipped by ServiceTitan (addendum §1.8 (a) and (e)).

### Blast radius of a mistake — the three worked examples
1. **Brewery / the birthday cake** (spec-stress-test §1): "The correct behaviour is to **defer the cake question and record a specification gap**, not to reason that cakes are 'probably fine.' The business has no written authority either way, and **improvising one is how an agent creates a promise the business did not make.**"
2. **Gym / the pregnancy freeze** (spec-stress-test §2): "The correct behaviour is to **escalate, not refuse**… **A refusal here would be a decision the business never authorised, delivered with the confidence of policy.**"
3. **Dental / the throbbing tooth** (spec-stress-test §4): "The correct behaviour is **immediate escalation with an urgent flag, answering neither half**… This is the case where correct behaviour is to **abandon the stated goal entirely**." And: "the episode was escalated on an urgency trigger, **which is a success and not a failure**."

### Behaviour when the rules are silent
> "**Behaviour when the business's rules are silent** — Proposed: **escalate, and record the gap as a specification defect. Never improvise a rule**" (brief §Open Architecture Questions). Note: listed as *proposed*, under open questions — not yet decided.
> "gaps recorded as **specification defects rather than guessed**" (brief §The Builder's Role).

### The trust thing the brief says is hardest, and it is an elicitation problem
> "**The builder's hard problem is elicitation, not generation.** The stress test found that **the least-documented content is the most safety-critical**: prohibitions, guard conditions, escalation thresholds and the operational rules (billing cut-offs, lead times, which exceptions are routinely granted) **frequently exist in no document at all.** The generic guardrail library covers the floor; everything above it must be extracted, with **contradictions surfaced** and gaps recorded as specification defects rather than guessed." (brief §The Builder's Role)

And the warning about asking directly (addendum §5.5): "Eliciting *'what must your agent never do'* by open question **will produce a dangerously short list.**"

**UX consequence `[INFERRED]`, and it is the dominant one:** the onboarding conversation cannot earn trust by asking the operator what to forbid. It must propose, show contradictions it found between their documents, and make gaps visible as named unknowns.

---

## 6. STAKES AND RISK LEVEL

**Stakes level, stated:** not hobby, not consumer, not currently regulated in V1. It is a **commercial B2B tool for small businesses that take money and change account state**, built by a solo developer with no commercial validation.
- "**No commercial moat is claimed.** … Commercial potential is unproven and probably modest for a solo builder, and **the project is not justified by it.**" (brief §Market Honesty)
- "This needs **no customers and no market**, only real business material… It tests the architecture claim and should run **before any commercial validation**." (brief §The Minimum Generalisation Test)

**Regulated industries named:**
- **Dental / healthcare** — the sharpest instance. Clinical rules verbatim: "**No clinical advice or diagnosis, ever** — explanation drawn solely from approved patient-information material · cost figures from the published fee guide, **always with the caveat that the final cost depends on clinical assessment** · a root canal always requires an assessment appointment first · … · **no record access without identity verification** · **no clinical detail over an unverified channel**" (spec-stress-test §4). Prohibited questions: "**Not permitted: symptoms, pain level, medical history. Asking about symptoms invites triage, and triage is clinical.**"
- **Legal** — researched and rejected as a candidate, but its derived requirements are recorded (addendum §1.6): Alabama Formal Op. 2026-01 (UPL risk, "the deploying lawyer is liable (Rules 5.5, 5.3, 8.4)"); Oregon Op. 2026-208 ("**supervises the vendor as a nonlawyer assistant** (Rule 5.3)"); Florida Op. 24-1 ("disclose AI; the lawyer owns everything the bot says"). Derived: "**AI disclosure on every channel; collect-and-screen only, no advice; conflicts check before substantive intake; Rule 1.18 confidentiality implying the vendor is contractually a supervised nonlawyer assistant with no training on client data.**" **Caveat recorded: "All three opinions were read via secondary summaries; the opinions were not fetched first-hand (an explicit evidence gap)."**
- **Fitness/medical data** — gym: "**Not permitted: any medical detail.** The agent may ask *whether a doctor's note can be provided*; it may never ask about the condition." (spec-stress-test §2)
- **Alcohol licensing / safeguarding** — brewery: "licensed maximum, not negotiable… **under-18s permitted until 20:00 only**" (spec-stress-test §1).
- **Chemicals** — garden centre: "**give pesticide or chemical advice beyond label guidance**" is a prohibition; "regulated chemical advice is correctly a *refusal* rather than a capability" (spec-stress-test §Q4).
- **Payments / financial** — gym direct debit, deposits, credit notes, "**no retroactive start**", "**requests inside five working days of the next direct debit take effect the following cycle**" (spec-stress-test §2). Brewery: "**Not permitted: … payment card details.**"

**Messaging-channel compliance** (addendum §1.4), which matters if V1 lands on SMS/WhatsApp rather than email:
- "**US A2P 10DLC is mandatory**: brand **$46 one-time**; campaign **$15 one-time + $10/mo** (Agents & Franchises **$30/mo**); carrier surcharges per segment. **2026 tightening** includes **EIN ≥15 days**, carrier-verifiable opt-in URLs, and **Reseller ID mandatory when registering on behalf of another entity**. Consequence: **per-tenant onboarding friction that bundled incumbents absorb and a solo developer would not.**"
- "**WhatsApp**: per-message pricing since 2025-07-01; from **2026-02-16** Meta charges 'AI Providers' **$0.0691/message** for non-template messages (**Italy first**). The definition of 'AI Provider' is loose — recorded as **tail risk**."
- **`[INFERRED]` this is a material argument FOR email as the V1 channel** — email carries none of this registration friction. The brief does not make the argument; it only records the friction.

**Data handling, stated:**
- "**Owning any system of record** — Out… External business systems stay authoritative" (brief §Scope).
- "**Long-term customer memory, cross-episode profiling, proactive outreach**" — Out (brief §Scope).
- Durable evidence is product data: "evidence is durable (**runtime evidence is product data, not operational logs**)" (addendum §3.1).
- Unresolved privacy/ownership question: "**Whether the target buyer requires runtime ownership** — Ask directly: *would you accept a hosted runtime holding your conversation data?*" (addendum §6, unknown 11).
- No-training commitment appears **only** inside the legal-vertical derived requirements, not as a product-wide statement.
- Data-residency / GDPR / SOC2 / DPA: **BRIEF SILENT.**

---

## 7. SCOPE BOUNDARIES

### In, for V1 — verbatim (brief §Scope)
- "The **reusable behavioural core**, complete, including guard conditions, authority classes, obligations, contracted actions with verification, and the generic guardrail library"
- "The **business specification model**: human-readable, diffable, versioned, with version-pinned knowledge"
- "**Episode lifecycle** with pending and resumable episodes, separated from resolution and from action evidence"
- "**Bounded multi-goal episodes** with explicit parking and resumption"
- "**The minimal builder**: conversation and sources → draft specification → validation and self-test → deploy"
- "**Grounded retrieval** with the two-tier distinction enforced and recorded"
- "**Durable structured episode evidence** with stable episode identity"
- "**Invariant evaluation checks** plus per-business criteria"
- "**The four generalisation businesses**, with all three measurements recorded"

### Out, explicitly — verbatim (brief §Scope)
See §3 above for the full list. The ones with direct UI consequences:
- "**Multi-tenant hosting, billing, onboarding automation, commercial packaging**" — **OUT**
- "**Domain-specific regulatory packs in V1 — the extension point exists; the packs do not**"
- "**Voice** — a separate, already-proven project. Channel is an adapter; **one channel ships for V1** and the core never learns which it is on"
- "**Platform-initiated outbound conversation**" — resumption arrives "as a further inbound interaction or an external system event, **never as outreach the platform decided to start**"

### Bounds within the in-scope items (brief §Multi-goal, deliberately bounded)
> "goals come **only** from the business's declared set; **the agent may not invent a goal**; **one goal is active at a time**, with parking and resumption both explicit; and there is **no decomposition of goals into agent-generated plans**."

### Deferred to architecture, not product
- "**The final resolution enumeration** — Deliberately deferred here; it follows from the runtime model" (brief §Open Architecture Questions)
- "How should the runtime interpret the specification?" / "Where do deterministic primitives end and model-driven behaviour begin?" / "How are authority, evidence, state, tools and evaluation represented?" / "What is configuration, what is an extension point, what is custom?" / "**Retrieval architecture, model strategy, the V1 channel**"
- "Product exploration is **closed**. These are the next stage." (brief §Open Architecture Questions)

---

## 8. BUSINESS MODEL, PRICING, ONBOARDING FUNNEL

**Product's own model and pricing: BRIEF SILENT, and deliberately so.** "**Multi-tenant hosting, billing, onboarding automation, commercial packaging**" are all in the Out list (brief §Scope). No signup, no trial, no paywall, no plan tiers, no activation gate is described anywhere.

**`[INFERRED]` UX consequence:** V1 has **no commercial funnel in the UI at all**. There is no signup/trial/paywall moment to design. The "activation moment" is a product-value moment, not a conversion moment (see §10).

**Market pricing recorded, as context only** (brief §Market Honesty; addendum §1.3): "**$99–199 per location per month inside software costing $400–600**, or outcome pricing at **$25 per converted lead**." Addendum adds Intercom $9.99/qualified lead, HubSpot ~$0.50/resolution, Agentforce ~$2/conversation, Podium $399–599/mo.

**Why outcome pricing is structurally unavailable to us** (addendum §2): "**outcome pricing requires measuring outcomes**, which requires the **join key and the evidence loop**… **a third party without the join key cannot price that way at all.**"

**The "onboarding" that does exist is the build flow, not a funnel** (brief §The Builder's Role):
> "**business conversation + source material → draft specification → validation and self-test → deployable instance**"

And: "The builder need not be an autonomous coding system; **it needs to make a new agent fast enough that the generalisation claim is testable.** Without it, this is a runtime plus an assertion that it can be configured." The reinstatement of the builder into scope was a user override (addendum §5.6): "**The builder is out of scope (the coach's cut) — Reversed by the user.** The ability to rapidly create a new business-specific agent is **central to the thesis**."

**Unit economics are an open unknown** (addendum §6, unknown 12): "**Cost to serve per episode** — Count per episode: turns, LLM calls, tool calls, tokens, cost; store on the episode record. **First real unit-economics number, replacing a guess.**"

---

## 9. TARGET VERTICALS NAMED

**The four canonical ones — the brief's own set, in the brief's own words** (brief §Executive Summary and §The Generic Interaction Pattern):

| Business | "A real request" (verbatim) | "What it stresses" (verbatim) |
|---|---|---|
| **Brewery** | "I want to host a 40-person event next month." | "Negotiated multi-constraint planning; no slots, no practitioners" |
| **Gym** | "I want to freeze my membership for two months." | "Account state mutation under policy; recurring commitments" |
| **Garden centre** | "This plant I bought is dying. What should I do?" | "Diagnostic advice; ambiguous goal; a liability boundary" |
| **Dental practice** | "I was told I need a root canal. What happens?" | "High-stakes grounding; mandatory override; explanation, not transaction" |

"These are not one workflow with four skins. **The claim is that they share behaviour.**"

The stress-test wordings differ slightly and are richer for example content: brewery *"I want to organize a 40-person event here next month"*; gym *"I need to freeze my membership for two months"*; garden centre *"My plant is dying. I bought it here two weeks ago."*; dental *"I was told I need a root canal. Can you explain what happens?"*

**The four deliberate failure cases — the best available example content for any "what it does when it is unsure" surface** (spec-stress-test, verbatim):
- Brewery: *"Can we bring our own birthday cake, and run until 10pm? It's for my daughter's 14th."*
- Gym: *"I'm pregnant, so I need six months."*
- Garden centre: *"It's a lavender in a pot on my balcony. It's gone grey and crispy. I water it every day."*
- Dental: *"It's been throbbing for three days and I can't sleep. Do I need to come in urgently or can it wait two weeks until payday?"*

**Important correction recorded** (addendum §5.6): "**'nursery' read as childcare (brief v1) — Mis-read.** It is a **plant nursery / garden centre** (the dying-plant request). The correction **materially strengthens the diversity argument**, because that request involves **no transaction at all**."

**Other verticals named, but as competitor territory or rejected candidates, NOT as our targets:** trades/home services (ServiceTitan, Podium), salon/spa & med-spa (Mindbody, Zenoti, Boulevard, Fresha), physio/allied health (Cliniko, Jane App), veterinary (ezyVet/IDEXX, Cornerstone, Covetrus, Vetstoria, PetDesk), legal (Clio, MyCase). **Do not seed templates from these** — brief §Scope: "**Any vertical framing**" is out, and addendum §5.4 records the physio/Cliniko recommendation as **withdrawn by user course correction** precisely for "optimising for API accessibility and producing exactly the narrow vertical product the user was avoiding."

Also noted and unexamined (addendum §5.3): "**internal operations** — one of the user's three *original* candidate classes… **It is not rejected; it is unexamined.**"

---

## 10. SUCCESS DEFINITION AND THE ACTIVATION MOMENT

### Named activation / aha moment
**BRIEF SILENT on an activation moment in the UX sense.** Neither document names a first-run aha, a time-to-value target, or a moment the operator "gets it."

**The nearest things the brief offers, in order of how usable they are as an activation moment:**

1. **The selftest pass / deployable instance.** "conversation and sources → draft specification → **validation and self-test** → deploy" (brief §Scope). The existing voice product's hard rule is the precedent: *"Selftest is the gate. No generated agent ships without `python selftest.py` passing in mock mode"* (project CLAUDE.md, not the brief). Addendum §4.3 flags its limitation: "`selftest_status` is a **build-time** quality gate standing in for a **run-time** quality signal."
2. **Setup effort falling.** "**Setup effort** — **wall-clock time and number of source artifacts to a passing self-test** — [fails if] effort does not fall materially across the sequence" (brief §The Minimum Generalisation Test). This is the brief's only time-to-value metric, and it is a *project* metric, not an operator-facing one.
3. **The first resolved episode.** `[INFERRED]` from the per-episode criteria below plus addendum §6 unknown 9: "**Whether a joined episode is cheap** — Run the narrowest end-to-end episode against one real external system: conversation → structured action proposal → deterministic execution → confirmation → an episode record carrying an episode ID and the external join key. **One happy path.**"

### What "working" looks like — verbatim (brief §Success Criteria)

**Per episode** — "computable from the record without a human reading it":
> "reached a declared resolution or a legitimate pending state; every business fact traceable to a pinned source; obligations complete before any action; actions taken only through contracts, with confirmation where required and **evidence of success recorded**; no conclusion drawn outside a declared authority; guards fired when their conditions were met; escalation reason recorded; no policy violation."

**Per business** — the three operator-facing numbers:
> "share of inbound episodes **resolved without a human**; share **reaching the intended action** — reported separately from the share **blocked by the business's own rules or capacity**, because **conflating them makes a business constraint look like an agent failure**; **human corrections per hundred episodes, and whether that falls over time**."

`[INFERRED]` **That middle clause is a direct dashboard requirement:** any operator-facing success number must separate *the agent failed* from *your own rules said no*. Reinforced by addendum §1.8: ServiceTitan's "70% including capacity constraints vs 90% excluding them — the dominant failure is that *the calendar had nothing to offer*… **not comprehension**."

**Per-business success definitions from the stress test** (quotable, operator-shaped):
- Brewery: "A provisional hold exists, an indicative quote has been issued, and the events manager has been notified — *or* a clear refusal citing the governing rule — *or* a deferral in which **everything needed has been collected, so the human needs no second contact.**"
- Garden centre: "**Advice alone, with no action and no claim, is a legitimate success here.**"
- Dental: "**or** the episode was escalated on an urgency trigger, **which is a success and not a failure.**"

**The usefulness test** (brief §The Minimum Generalisation Test): "take each business's *real* inbound requests — **public enquiries, reviews, published FAQs, an operator's own inbox** — and measure the share reaching a correct resolution without a human."

**And the unknown that most threatens any success UI** (addendum §6, unknown 3):
> "**Whether operators can name an observable failure** — Ask the operators *'how would you know the agent did a bad job?'* and record the answer **verbatim, without prompting.** If they cannot name one, the evidence→evaluation→promotion loop **has no customer-side signal** and must be rebuilt around our own assertions only."

---

## 11. STATED UX, DESIGN, OR INTERFACE OPINIONS

**Almost entirely BRIEF SILENT.** No screens, no layout, no visual direction, no component opinion, no accessibility statement, no platform (web/desktop/mobile) statement. What exists:

1. **The specification must be human-readable.** "The specification must be a **first-class, human-readable, diffable artifact**." (brief §The Builder's Role) — the single strongest UX requirement in the brief.
2. **Diffable, with teeth.** "Control flow… lives **in the specification only**: interpretable, diffable, assertable, promotable." (addendum §3.3 C1) And the reason version-pinning exists: "a specification diff **explains nothing**" without it (brief §The Business-Specific Specification).
3. **Disagreement must be cheap.** "make **disagreement cheap to express and fast to propagate**" (addendum §3.1) — the clearest behavioural mandate for the review surface.
4. **Contradictions surfaced, gaps named.** "with **contradictions surfaced** and gaps recorded as **specification defects** rather than guessed" (brief §The Builder's Role).
5. **Human review in the loop on every build.** "**Human review stays in the loop.**" (brief §The Builder's Role)
6. **Degraded answers must be distinguishable.** General domain knowledge "May come from the model, **must be marked as such** in the episode record" (brief §Grounding has two tiers). Garden-centre evidence field: "**for every piece of advice, whether it was business-authoritative or general knowledge**" (spec-stress-test §3).
7. **Never put measurement on the reply path.** "Evaluation timing — **Leave empty: synchronous per turn** — Never put measurement on the reply path to learn what a recorded episode yields afterwards" (addendum §3.4).
8. **Personalisation warmth is refused.** "Personalisation — **Leave empty: LLM-generated** — **Buys warmth, costs a call, adds variance to a reply otherwise controlled**" (addendum §3.4). `[INFERRED]` this is a *tone* decision smuggled in as an architecture decision: the generated agent is controlled and consistent, not warm-by-improvisation.
9. **Channel-independence is a requirement.** "**Channel is an adapter; one channel ships for V1 and the core never learns which it is on**" (brief §Scope). `[INFERRED]` the operator-facing UI must not be channel-shaped either.
10. **Text removes a whole class of concern.** "Turn segmentation — **Leave empty: model-based boundary, streaming-continuous** — In text, turns are **discrete client messages. The whole axis is a voice artifact**" (addendum §3.4). Addendum §4.5: the voice machinery items "are **not** 'modality-specific logic leaking into the core' — they are concerns that **cease to exist** in text. **Nothing has to be abstracted; they are simply out of scope.**"

---

## 12. FROM spec-stress-test.md ONLY — open risks (NOT decided truth)

Listed as the stress test itself flags them. Treat every item as contested.

1. **The exercise proves expression, not behaviour.** "It validates that the schema can *express* four dissimilar businesses. It does **not** validate that an agent built from such a specification *behaves well*, nor that the specifications are right — **they are my constructions, not any real business's rules.**" (§Verdict, honest note)
2. **The practised-vs-printed policy gap is the likeliest place all four specs are wrong, and "only a real operator can close it."** (§Verdict; §Q9)
3. **Four of the eight required changes are structural** and were discovered late: replace the resolution model (`pending` missing); multi-goal episodes; a pre-emptive gate before goal recognition; decision authority classes. (§Verdict table)
4. **The single-goal assumption failed.** "Multi-goal and goal-switching are **the normal case, not an edge case**." (§Q5a)
5. **"There is no step zero."** The eleven-step pattern "begins at 'understand what the person wants,' which is **already too late**." (§Q5b)
6. **"Decisions permitted" conflates two kinds of authority** — cause vs fault. (§Q5c)
7. **Cross-session continuation was wrongly scoped out.** "**I was wrong to place this out of scope.**" (§Q5d)
8. **"Information needed" is overloaded** — obligations vs diagnostic evidence vs (dental) nearly empty. "A single field cannot carry all three meanings." (§Q1, §Q5e)
9. **The resolution kinds were partly forced.** "Partly forced… **two are wrong and one is missing.**" (§Q6)
10. **A spec diff can be uninformative** — two agents differ by a revised leaflet with identical specs. "**Nearly, but not as specified.**" (§Q7)
11. **The builder does NOT have enough input for two of the four businesses.** "**No — for two of the four.**" Gym: operational rules exist nowhere. Dental: "**no**… the entire prohibition list and the full urgency-trigger set — the most safety-critical content — **exist in no document.**" (§Q8)
12. **Prohibitions cannot be elicited from scratch.** (§Q8) — **note the proposed remedy was later REPLACED, see §13 item 3.**
13. **"None required custom implementation" is itself suspicious.** "a good result for the thesis and **also a reason for suspicion — four examples is a thin basis** for concluding that the third level is never needed." Custom work expected first "around **verified record access**" in dental. (§Q4)
14. **Nine things likely to stay implicit in the owner's head** (§Q9), the largest being the printed/practised gap.

---

## 13. ADDENDUM REVISIONS AND OVERRIDES — FLAGGED LOUDLY

### ⚠️ A. The addendum does not override the brief — it records the trail BEHIND it
Addendum header: "Companion to `brief.md`. **The brief states conclusions; this file holds the evidence, the rejected alternatives and the reasoning behind them. It deliberately does not restate the brief.**" Brief footer: "**Supporting depth in `addendum.md`.**" **Where they appear to differ, the brief is the conclusion and the addendum is the superseded step.** Four cases where reading the addendum alone would mislead:

### ⚠️ B. SUPERSEDED IN THE ADDENDUM ITSELF — do not build UI on these
1. **The resolution enum `resolved_informational | resolved_actioned | refused | escalated | pending`** (addendum §5.6, from spec-stress-test §Q6) is **superseded**. The brief says: "Resolution families are deliberately **not fixed as a final enum**… Candidate families, **provisional**: *served with information*, *served with action*, *declined under a declared rule*, *handed to a human*." (brief §Three orthogonal dimensions) → **Use the plain-English provisional four for copy, and mark them provisional.**
2. **The earlier enums are doubly dead:** "Fixed disposition set **answered | action taken | escalated | out of scope**" was "**Too appointment-specific**"; "**fulfilled | committed | informed | deferred | refused**" failed because "**fulfilled/committed did not separate cleanly** and **deferred was carrying three unrelated meanings**." (addendum §5.6)
3. **⚠️ The per-vertical prohibition library is DEAD.** spec-stress-test §Q8's headline remedy — "**a prohibition and escalation library per business category**" — was **replaced** (addendum §5.5) by "a **generic, domain-neutral guardrail library in the core**… **plus optional domain packs as extension points, never core architecture** — and with **no packs in V1**. Reason: a per-category library makes vertical knowledge a core dependency, **reintroducing the vertical framing the project had just rejected**, and it scales as the number of categories rather than as the architecture." **UX consequence: there are NO per-vertical starter templates in V1.** The five generic guardrails are the only pre-filled content. The *motivation* for the library still stands ("the most safety-relevant finding of the stress test").
4. **The physio/Cliniko vertical recommendation is WITHDRAWN** by user course correction (addendum §5.4), with the standing rule: "research must answer *'is there a broad SMB class of problems where a reusable conversational-agent architecture creates meaningful value'*, **not** *'which vertical has the easiest public API'*. **The user does not need an unsaturated vertical.**" Recorded as "the **third occurrence of the same bias**" (architecture-convenience bias).
5. **"Anything spanning sessions is out of scope" was WRONG** — explicit coach self-correction (addendum §5.7): "**as the user suspected.** Three of the four stress-test examples **require** cross-session continuation… **Anything that defers or awaits a document is inherently multi-session, and that is most of the interesting behaviour.**" Diagnosis: "**the absence of a `pending` outcome kind from the coach's first model is what hid the finding. A missing enum member silently defined a capability out of existence.**"
6. **"The builder is out of scope" was REVERSED by the user** (addendum §5.6) — see §8 above.
7. **"Capacity blocked as a platform invariant"** → "**It is a booking example, not a platform invariant.**" **"Non-FAQ share as a product metric"** → "**It is a proof/evaluation concept, not a universal product metric.**" (addendum §5.6) — `[INFERRED]` neither belongs on an operator dashboard.
8. **text-first vs voice REOPENED** (addendum §5.4) — see §0 above.

### ⚠️ C. ADDENDUM-ONLY MATERIAL ABSENT FROM THE BRIEF, material to UX
1. **The fencing/trust-deficit finding** (§1.7) — the strongest empirical argument that trust is the product's real axis. Not in the brief.
2. **"The real moat is not conversation quality or explainability — it is write access to the calendar with live capacity"** (§1.8). Not in the brief.
3. **The trust-feature audit** (§1.8) — (a)(b)(c)(e) all shipped by incumbents; only (d) counterfactual replay unoccupied. Not in the brief.
4. **"Appointment intake is closed as a commercial opportunity"** — COACH VERDICT (§2). The brief states only "No moat is claimed."
5. **The fabricated-statistics integrity warning** (§1.9), "**the most reusable lesson in the file**": Swiss Monkey's uncited "60% of practices receive patient complaints within the first month" / "40% abandon AI systems within three months" — "**Swiss Monkey sells remote human dental front-office staffing — the product those statistics argue for.**" Generalised rule: "when a statistic is the exact number needed to justify a purchase, **check who sells the alternative before citing it**." → **UX consequence: no abandonment, complaint-rate or missed-opportunity statistic may appear in any copy.**
6. **Current-codebase facts** (§4) that bound what a UX spec can assume exists today: durable storage is two SQLite tables (`sessions`, `built_agents`) and "there is **no table capable of recording a conversation, a turn, a tool call, an outcome or a latency**"; "**build-time facts are durable, run-time facts are ephemeral**"; "the improvement loop… currently has **zero substrate; the circuit is physically open.**" → **An operator-facing episode review / quality surface has no backing store today.**
7. **The regeneration trap** (§3.2, §5.2): "the 'generated agents are disposable' model has an unstated precondition — **nobody ever edits the generated output.** The moment a developer tweaks a generated `prompts.py`/`tools.py` in place, **regeneration destroys the work**." → `[INFERRED]` the operator must only ever edit the specification, never an output; the UI must give them no other edit surface.
8. **The lead-qualification evaluation trap, said to generalise** (§5.1): "Where false negatives are invisible, an outcome-driven improvement loop **rewards drift toward strictness**: conversion among passed leads rises while total revenue falls." → `[INFERRED]` any operator-facing "it's getting better" number must not be a pass-rate.
9. **Fourteen open unknowns requiring primary evidence** (§6), each with a named settling experiment. Unknowns 1, 3 and 11 are operator-facing and are UX research questions, not engineering ones.
10. **Deployment-ownership orthogonality warning** (§3.3): "'no generated application code' and 'one process serves everyone' are **orthogonal concerns and must not be coupled**… **Nothing in the session proved multi-tenancy.**" → consistent with multi-tenant hosting being out of V1 scope.

---

## Appendix — the brief's own structural vocabulary, for reference

**The behavioural chain** (brief §The Behavioural Chain):
> "**goal → information gathering → reasoning / decision → allowed action → verification → outcome**"
with "A **guard check** runs ahead of the chain."

**The business specification's eleven sections, verbatim** (brief §The Business-Specific Specification) — the de-facto information architecture of whatever the operator reviews:
Identity · Goals · Knowledge · Obligations · Diagnostic inputs · Rules · Authorities · Tools and actions · Guard conditions · Escalation policy · Evaluation criteria.

**The three-level variation contract** (brief §The three-level variation contract):
1. "**Configuration / specification** handles normal variation — the expected path, covering the great majority of cases."
2. "**A supported extension point** handles capability that recurs across businesses but is structurally unlike configuration."
3. "**Custom implementation** handles genuinely novel capability, and is **the exception, never the workflow**."
Plus: "Custom code may be a leaf. **It may never be control flow** — control flow stays in the specification, where it can be **read, diffed, evaluated and reverted**."

**Guard families** (brief §Guard conditions): "**urgency**, **authorisation failure**, **policy violation**, **unsupported request**, **identity problem**, and any other declared guard."

**Escalation reason classes** (spec-stress-test §Q6): "**urgency, authority gap, dispute, verification failure, out of competence**."
