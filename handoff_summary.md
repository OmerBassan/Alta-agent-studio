# Alta Agent Studio - Handoff Summary

This document summarizes the recent architecture changes, decisions, and remaining challenges in the Alta 2.0 platform. It is designed to be handed off to another Claude instance for context continuation.

## 1. Context & Goals
The user wanted to streamline the `builder` agent (which interviews the user and generates a voice agent) to be cheaper, faster, deterministic, and strict about following the `alta:ask` card UI flow. We also addressed the live runtime of the *generated* agents (Vapi + LangGraph) to fix latency, hallucination, and verbosity issues during live test calls.

---

## 2. Changes & Modifications Already Implemented

### A. Cost Reduction & Model Swap
- **Change:** Changed `BUILDER_MODEL` in `builder_platform/builder.py` from `"sonnet"` to `"haiku"`.
- **Impact:** Slashed the cost per build from ~$3.00 down to ~$0.15, while running significantly faster.

### B. Discovery Phase Strictness (MISSION Card)
- **Problem:** The builder hallucinated questions, skipped phases, and sometimes failed to output the strict JSON `alta:ask` UI cards.
- **Change:** Updated the system prompt in `builder_platform/builder.py` and `skill_steps/step1_discovery.md`. 
- **Impact:** The builder is now strictly mandated to use an `alta:ask` card for the MISSION phase and TEST_DETAILS phase. It is forbidden from mixing phases on a single card and is forced into a "speed run" (2-3 questions max).

### C. UI Narration Bloat & Silent Editing
- **Problem:** The builder wasted tokens and UI space narrating its tool usage ("Let me edit this file...").
- **Change:** Updated `builder.py` prompt instructions to ban internal narration. Updated `app.py` logic (`_INTERNAL_LEADIN_RE`) to strip out `.py` references and work-narration from the UI stream. 
- **Impact:** The builder edits silently. The user only sees the tool chips and the final success message.

### D. Lean Architecture (`tools.py` & `README.md`)
- **Problem:** The builder wasted tokens regenerating boilerplate files and trying to rewrite Python tool logic (`tools.py`).
- **Change:** Added explicit bans in `SKILL.md` forbidding the agent from editing `tools.py` or creating `README.md`. 
- **Impact:** The generated agent now relies exclusively on the robust, pre-built generic tools (e.g. `book_appointment`, `issue_refund`).

### E. Ngrok Auto-connect
- **Problem:** `run.bat` opened ngrok in a separate window, which frequently failed to connect or pass the URL back to Vapi.
- **Change:** Modified `builder_platform/tunnel.py` to auto-spawn ngrok directly via Python (`subprocess.Popen(["ngrok", "http", str(runtime_port)])`) if no tunnel is detected when the user clicks "Start call".

### F. Explicit Build Completion Status
- **Problem:** The builder didn't explicitly signal when the background build was entirely finished.
- **Change:** Updated `builder.py` to force the agent to emit a deterministic `> [!SUCCESS] BUILD COMPLETE! ...` GitHub alert after the selftest passes.

---

## 3. Pending Problems & Required Fixes (The Next Step)

A test call was made to the generated "Roast & Door" agent, which revealed three issues in the live LangGraph/Vapi runtime. Here is the diagnosis for Claude to fix:

### Problem 1: Filler Latency (Dead Air)
- **Symptom:** Filler sounds ("Hmm...", "Let me check...") play right before the LLM answer, rather than instantly bridging the gap.
- **Root Cause:** Vapi buffers incoming SSE text until it hits a terminal punctuation mark (`.`, `?`, `!`). The generic fillers in `runtime.py` and `boilerplate/config.py` use ellipses (`Hmm… `), causing Vapi to buffer them and wait for the real LLM answer to complete the sentence.
- **Required Fix:** Replace all ellipses in filler strings with periods (e.g. `"Hmm. "`) across `builder_platform/runtime.py` and `boilerplate/config.py`.

### Problem 2: Hallucination of Mission Promises
- **Symptom:** The agent hallucinated that Roast & Door doesn't offer free sample coffee, even though the user included it in the initial prompt.
- **Root Cause:** The builder LLM failed to copy the "free sample" offer into the `FACTS` block of the generated `config.py`. The runtime strictly answers from `FACTS`, so missing info causes hallucination.
- **Required Fix:** Update `skill_steps/step4_build.md` to explicitly instruct the builder: *"CRITICAL: Extract ALL specific offers, pricing, discounts, and free samples from the mission into the FACTS block. If it is omitted from FACTS, the agent will hallucinate."*

### Problem 3: Long Sentences (Verbosity)
- **Symptom:** The generated voice agent speaks in long, compound sentences, violating natural conversational norms.
- **Root Cause:** The system prompts in `boilerplate/prompts.py` gently suggest "1-3 sentences", which models stretch into massive paragraphs. 
- **Required Fix:** Update `build_knowledge_system` and `build_chitchat_system` in `boilerplate/prompts.py` to enforce extreme brevity: *"CRITICAL: Limit answers to exactly 1 or 2 extremely short sentences. Never speak more than 20 words."*
