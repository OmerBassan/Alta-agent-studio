# Alta Agent Studio — Reviewer Demo Script

A 5-minute walkthrough proving the deliverable: **a platform where you chat with
an AI builder that creates and edits a voice AI assistant in natural language**,
then call that assistant and hear it qualify a lead.

There are two paths. **Path A** calls a pre-built agent so you hear voice in under
a minute. **Path B** is the real deliverable — describe → generate → call → edit →
call again.

---

## 0. Launch (once)

1. Run `run.bat` (Windows) or `./run.sh` (macOS/Linux). It builds the venv,
   installs deps, and starts the server on **http://localhost:8100**.
2. Open that URL. A first-run setup overlay asks for two keys:
   - **Anthropic API key** — powers the AI *builder*.
   - **OpenAI API key** — powers the generated *agent's* brain on the call.
   Vapi (the voice transport) is pre-provisioned; no key needed from you.
3. For a real phone/web call you also need ngrok running (see `README.md`). The
   selftest and the whole build flow work without it — only the live call needs it.

---

## Path A — hear the voice now (pre-built agent)

A fully-built, selftest-passing agent ships in `Generated_Agents/BassanBrewerySDR/`
— **Tom from Bassan Brewery**, an SDR that calls leads and qualifies their
drink-ordering needs.

1. In the top bar, click the **session-id pill**, type `BassanBrewerySDR`, press
   Enter.
2. The status orb lights (the agent is found and its selftest already passed).
3. Click **Call**. Talk to Tom.
4. He qualifies you on four things — roughly monthly volume, your drink mix,
   when your current supplier contract renews, and whether you want an annual /
   monthly / one-off / as-needed deal — then routes a hot lead to the sales team.
   Say **"not interested"** firmly and he thanks you and ends the call — no nudging.

---

## Path B — the deliverable: build, call, edit, call again

1. Click the session pill and set a **fresh** id (e.g. `demo1`), Enter. Empty chat.
2. Paste one of the **cold rehearsal prompts** below into the chat.
3. The builder runs a short guided design conversation — mission, qualification,
   objections, close, boundaries, review. Answer each card (a sentence each is
   fine). Keep it moving.
4. At the **Review** card, click **Looks great** to build — or click **I'd change
   something**, edit the design text inline, and **Submit for approval**. The
   builder writes the project, runs its selftest, and lights the orb.
5. Click **Call** and talk to your new agent.
6. **Prove the edit loop:** end the call, tell the builder one change (e.g. "ask
   for their budget before booking"), approve, and **Call again** — the runtime
   respawns on the edited files, so the change is live on the next call.

---

## Cold rehearsal prompts (paste verbatim)

**Rehearsal 1 — beverage SDR (mirrors the pre-built agent):**

> I run a beverage distributor. Build a voice agent that calls restaurant owners
> who left their details, checks how much they order each month, what drinks they
> buy, when their current supplier contract ends, and whether they'd sign an
> annual deal — then routes hot leads to my sales team.

**Rehearsal 2 — solar consultation booker (different domain):**

> Build a voice assistant for my solar company. It calls homeowners who requested
> a quote, qualifies whether they own the home, their average electric bill, the
> age of their roof, and their timeline to install, then books a consultation
> with one of our reps.

---

## What "passing the demo" looks like

- The builder held a natural design conversation and produced a working agent
  **without you writing code**.
- `python selftest.py` inside the generated agent exits 0 (the platform enforces
  this before the orb ever lights — an unproven agent is never callable).
- On the call the agent speaks first, asks **one** qualifying question per turn,
  stays on script, and ends gracefully on a firm no.
- An edit in chat changes the agent's behavior on the very next call.
