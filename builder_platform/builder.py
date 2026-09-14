# -*- coding: utf-8 -*-
"""The AI Builder: a headless Claude Agent SDK session running the
voice-agent-architect skill, generating voice agents into isolated workspaces.

Architecture (Day 2 AM of the plan):

  skill delivery   SKILL.md is INJECTED into the system prompt (claude_code
                   preset + append). Deliberately NOT skill auto-discovery:
                   the architect instructions must always be active, not
                   depend on the model invoking a Skill tool, and a duplicated
                   skill bundle under .claude/skills/ is a drift trap (we found
                   a stale one during cleanup).

  privileged ops   The two operations the agent must not do by hand are SDK
                   MCP tools backed by deterministic platform code:
                     instantiate_boilerplate -> shutil.copytree (wholesale copy)
                     run_selftest            -> subprocess gate, forced MOCK
                                                mode, bounded timeout.
                   Bash is disabled outright.

  enforcement      permission_mode="default" with Write/Edit NOT pre-approved,
                   so every file mutation falls through to the can_use_tool
                   callback (docs: acceptEdits would BYPASS the callback).
                   Writes: only inside the session's generated project, never
                   an engine file. Reads (Read/Glob/Grep): allowlisted to the
                   skill surfaces + own workspace — the repo also holds live
                   secrets (builder_platform/.env, generated agents' credentials) the
                   builder has no business reading.

State fields: a BuilderSession holds `project_dir` (writer: the
instantiate_boilerplate tool, exactly once; readers: the write policy and the
selftest gate; lifecycle: lives for the session, one generated project per
session) and `selftest_passed` (writer: run_selftest; reader: the platform's
hand-over gate; reset by any subsequent write to the project).
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from pathlib import Path
from typing import Any, AsyncIterator, Optional

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

# Load the repo-root .env into os.environ BEFORE any module-level env read below
# (and before the SDK spawns its subprocess, which inherits os.environ). This
# import IS the bootstrap — keep it above the configuration block.
import env_bootstrap  # noqa: E402,F401

# The deterministic engine (paths, write/read policy, instantiate, selftest
# gate) is the single source shared with claude_plugin/'s MCP server + guard
# hook — see builder_core.py's module docstring. Re-exported by name here so
# app.py and the test suite keep importing them from `builder` unchanged.
from builder_core import (  # noqa: E402,F401 — some re-exported for app.py/tests only
    REPO_ROOT, WORKSPACES_DIR, GENERATED_AGENTS_DIR, SKILL_PATH, ENGINE_FILES,
    MAX_SELFTEST_RUNS, _MARKER_NAME,
    write_denial, read_denial, sanitize_project_name, discover_project,
    instantiate_project, has_persisted_pass, run_selftest_gate,
    _write_pass_marker, _clear_pass_marker,
)

# --- configuration (one place, env-overridable) ------------------------------

BUILDER_MODEL = os.environ.get("BUILDER_MODEL") or "sonnet"  # Default to sonnet; cache system prompt to reduce costs

# Thinking budget — clamped to {low, medium}; anything else (typos, "high",
# "max") silently degrades to "low". The clamp is code, not advice: a $4 proof
# run traced back to unbounded thinking, and the cost target is <=$1. Default is
# "medium": the discovery/build turns reason better (fewer skipped phases, more
# reliable FACTS extraction) at a still-bounded cost — "high"/"max" stay barred.
BUILDER_EFFORT = os.environ.get("BUILDER_EFFORT", "medium").strip().lower()
if BUILDER_EFFORT not in ("low", "medium"):
    BUILDER_EFFORT = "low"

# Agentic-turn ceiling per client message. The observed build turn peaked at
# ~19 tool uses (6 file edits + 2 selftest runs + todos) on Haiku; a ceiling
# below that makes a LEGITIMATE build hit the wall and fail (an unstable build,
# not a runaway). 24 leaves real headroom for the instantiate + edits + selftest
# + one fix-and-rerun path without licensing a runaway session.
BUILDER_MAX_TURNS = int(os.environ.get("BUILDER_MAX_TURNS", "24"))


# --- the platform brief appended (with SKILL.md) to the system prompt --------

PLATFORM_BRIEF = """
# Platform Execution Context

You are the AI Builder inside the Alta voice-agent platform. The client is a
NON-TECHNICAL business owner in a guided web chat. They see ONLY your plain text
and your question cards — never reasoning, files, or code.

BOOTSTRAP — before answering the FIRST message: Read `SKILL.md` (repo root).
It is slim and indexes step files under `skill_steps/`; read each step file
EXACTLY ONCE, at the moment SKILL.md's schedule says you need it. Never re-read
a file already in context. Never mention any of this to the client.

## Brevity and silence (hard rules)

- Client-visible prose is capped at ~40 words per turn: one short reflect-back
  sentence, then the card. No headings, bullets, or markdown ever.
- NEVER narrate internal work. Forbidden in client text: "Reading…", "Now
  I'll…", "Let me check…", file names, tool names, step numbers. The UI shows
  progress chips for tool calls.
- The BUILD turn (first instantiate) shows exactly TWO text blocks: one before the
  first tool call ("Building your agent now — this takes a couple of minutes.")
  and, ONLY AFTER selftest passes, exactly this closing block:
  `> [!SUCCESS] BUILD COMPLETE! The agent has passed the selftest. Click the "Start call" button below to activate it.`
- EVERY OTHER tool call (re-running selftest, editing, checking status) gets
  ZERO lead-in text — the tool chip already says what's happening. Never invent
  "Running the test now" / "Let me update that"; call the tool silently and
  speak only once you have its result.
- Internals NEVER surface: no state machines, config keys, model names, or
  architecture terms. Say the plain-language outcome instead.
- Enforced in code: client text with a `*.py` name, a CAPS_UNDERSCORE
  identifier, or work-narration is stripped — say only WHAT changed, once.
- Apply sane defaults silently (mock tools, English-only); never ask about them.

## The agents you generate are HUMAN-LIKE VOICE agents

Everything they say is heard, not read: short, warm, contractions, no
lists/markdown/URLs, acronyms as spoken, ONE question per turn. The review
playbook follows the same law — plain numbered scenes, quoted lines.

## The guided flow — ONE phase per card (via alta:ask)

The SPINE, in order — its keys are the ONLY valid `phase` values (step1
defines each): 1 mission, 2 qualification, 3 objections, 4 close,
5 boundaries, 6 test_details (made-up name/phone/email), 7 review (no card).

ADAPTIVE TURN SEQUENCE: Turn 1 always ends with the `mission` card, even just
to confirm a mission the client already gave. Then walk phases 2-5 in order:
covered by the mission answer -> SKIP the card, fold a one-line reflect-back
into prose ("Got it — I'll use your price-lock line for pricing."); not
covered -> present that phase's card, ONE question, default stated in
`intro`/`hint` for a quick confirm-or-correct. One follow-up per card max,
then default and move on — never fake "covered" to skip faster. Then
`test_details`. Then phase 7 (review + PLAYBOOK).
Never mix two phases on a card. Advance in order, never back.
Each asking turn ends with EXACTLY ONE strict-JSON block, always last. Turn 1 MISSION format:

```alta:ask
{"phase":"mission","step":1,"of":6,"kind":"questions",
 "questions":[
   {"id":"mission_details","label":"Tell me about this agent — the company, what it does, who it calls...","hint":"e.g. We call leads who received a free sample to convert them."}
 ]}
```

For `test_details` use `"phase":"test_details"`, `"step":6`, questions for name/phone.

`phase` must be a spine key; non-question turns emit no block. After phase 6,
present the PLAYBOOK (the whole call as a plain spoken script) and end with:

```alta:ask
{"phase":"review","kind":"approve","intro":"Here's how the call will go — does this look right?","approve_label":"Looks great — build it","revise_label":"I'd change something"}
```

On approve, build. On revise, apply the edit and re-present.

## Edit turns (a project already exists)

A change request to a built agent is NOT a build: no discovery, no step
files, no references, no codebase scanning. Read ONLY the domain files you
edit (usually prompts.py, config.py), make the smallest edit, run_selftest,
then confirm in one short line. Sole exception: scripting NEW spoken lines
may read ONE phone-craft file from references/playbook.

## Building (platform-wired)

1. INSTANTIATE only via the `instantiate_boilerplate` tool; VERIFY only via
   `run_selftest` — done means PASS. The selftest tool allows at most one
   fix-and-rerun; if it still fails, report the failure plainly and stop.
2. No shell. Writes only to domain files in your generated project (engine
   files are enforced read-only). Read ONLY the files you will edit.
3. Skip catalog promotion. Always pass explicit repo-root-relative paths.
4. The agent ships behind the Vapi voice runtime: the voice style pass, the
   FILLER_THINKING bank, and a real OPENER (spoken at pickup) are NOT optional.
"""


def build_system_prompt(project_dir: Optional[Path] = None) -> dict:
    # The brief must stay SMALL: the SDK passes the system prompt on the CLI
    # command line, and Windows caps that at ~32K chars (WinError 206). The
    # 40KB skill text therefore enters context via the bootstrap Read in
    # PLATFORM_BRIEF, never via this append.
    if not SKILL_PATH.is_file():
        raise FileNotFoundError(f"skill not found: {SKILL_PATH}")
    append = PLATFORM_BRIEF
    if project_dir is not None:
        # One line, session-specific: without it a reattached session (lost
        # tab / server restart) greets with the discovery wizard instead of
        # recognizing the project already exists — costs a full wasted turn
        # to correct. Cheaper to say it once here than have the user say it.
        append += (f"\n\nA project already exists at {project_dir} for this "
                   f"session. Do not start discovery. If the client's message "
                   f"already says what to change, apply it directly per the "
                   f"Edit turns rules — never re-ask; otherwise ask what they "
                   f"want to do with it (review, edit, run selftest).")
    return {
        "type": "preset",
        "preset": "claude_code",
        "append": append,
    }


# --- the session --------------------------------------------------------------

class BuilderSession:
    """One client <-> builder conversation bound to one workspace directory.

    Usage:
        session = BuilderSession("some-session-id")
        await session.start()
        async for event in session.send("I need an SDR agent for ..."):
            ...  # {"type": "text"|"tool"|"result", ...}
        await session.close()
    """

    def __init__(self, session_id: str,
                 workspaces_root: Path = WORKSPACES_DIR,
                 db: Optional[Any] = None) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_\-]{1,64}", session_id):
            raise ValueError(f"unsafe session_id: {session_id!r}")
        self.session_id = session_id
        self.workspace_dir = (Path(workspaces_root) / session_id).resolve()
        self.project_dir: Optional[Path] = None
        self.selftest_passed = False
        # writer: do_run_selftest (increments); reset: send(), at the start of
        # every client message; reader: the MAX_SELFTEST_RUNS cap check. The
        # cap's intent — "run + one fix-and-rerun", verification not
        # rumination — is PER CLIENT REQUEST: counted per session it locked
        # every post-build edit out of re-verification (the button-stays-
        # disabled-after-edit bug).
        self._selftest_runs = 0
        self._client: Optional[ClaudeSDKClient] = None
        # Optional StorageManager: persistence bookkeeping only. The DISK
        # marker (has_persisted_pass) stays the authoritative call gate — the
        # DB cannot see out-of-band file edits; the surface hash can. None
        # (the default) keeps the class unit-testable with no DB.
        self._db = db

    # -- privileged operations (plain methods, unit-testable) -----------------

    async def do_instantiate(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.project_dir is not None:
            return _text(f"ERROR: project already exists at "
                         f"{self.project_dir} — this session builds one "
                         f"agent; edit it instead.")
        try:
            dest = instantiate_project(str(args.get("project_name", "")),
                                       self.workspace_dir)
        except (ValueError, OSError) as exc:
            return _text(f"ERROR: {exc}")
        self.project_dir = dest
        self.selftest_passed = False
        if self._db is not None:
            try:
                self._db.register_agent(
                    session_id=self.session_id,
                    agent_name=dest.name,
                    project_path=str(dest),
                )
            except Exception as exc:  # bookkeeping must never fail the build
                print(f"[builder] storage register_agent failed: {exc!r}",
                      flush=True)
        # Deadlock fix: ship a fillable .env, not just the template. Without it
        # the operator has no per-agent place to put OPENAI_API_KEY and the
        # agent silently demos in MOCK forever. (Runtime precedence unchanged:
        # the parent process env — the repo-root .env — still wins.)
        env_example = dest / ".env.example"
        env_file = dest / ".env"
        if env_example.is_file() and not env_file.exists():
            shutil.copyfile(env_example, env_file)
        return _text(
            f"Project created at {dest} (exact copy of boilerplate/).\n"
            f"Editable domain surfaces: config.py, tools.py, prompts.py, "
            f"README.md, .env.example, corpus/new integration files. Engine files "
            f"AND selftest.py (fixed, config-derived) are read-only — the selftest "
            f"adapts to your config.py automatically, so never touch it.")

    async def do_run_selftest(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.project_dir is None:
            return _text("ERROR: no project yet — call "
                         "instantiate_boilerplate first.")
        if self._selftest_runs >= MAX_SELFTEST_RUNS:
            # Hard cap, enforced in code: the gate verifies, it does not debug.
            # Unbounded fix->test-loops were a major token sink in proof runs.
            return _text(
                f"ERROR: validation limit reached ({MAX_SELFTEST_RUNS} runs this "
                f"session). Stop iterating — tell the client plainly which "
                f"check failed and what you recommend; do not attempt more "
                f"fixes. IMPORTANT: DO NOT use the words 'selftest', 'boilerplate', "
                f"or 'codebase' in your explanation to the user, as they will be "
                f"filtered and hidden. Say 'validation checks' instead.")
        self._selftest_runs += 1
        # Run the REAL gate: the generated agent's fixed, domain-agnostic
        # selftest.py in a forced-MOCK subprocess. (Previously stubbed to
        # always-pass while the test was demo-coupled and looping; the test is
        # now config-derived and stable, so the gate is live again.)
        passed, output = await asyncio.to_thread(
            run_selftest_gate, self.project_dir)
        self.selftest_passed = passed
        if self._db is not None:
            try:
                agent = self._db.latest_agent(self.session_id)
                if agent:
                    self._db.update_selftest(
                        agent["id"], "passed" if passed else "failed")
            except Exception as exc:  # bookkeeping must never fail the gate
                print(f"[builder] storage update_selftest failed: {exc!r}",
                      flush=True)
        if passed:
            _write_pass_marker(self.project_dir)
            # The transcript tail is diagnostic material: on PASS there is
            # nothing to diagnose, and feeding it back only burns context the
            # builder still needs for the edit loop.
            return _text("SELFTEST PASS — the agent's full scripted "
                         "conversation and every invariant check are green.")
        # The failing assert + verdict live at the very end of the output; a
        # bigger tail only gives the builder more to ruminate about.
        return _text(f"SELFTEST FAIL\n\n{output[-1200:]}")

    # -- SDK MCP tools (thin closures delegating to the methods above) --------

    def _make_platform_tools(self):
        session = self

        @tool("instantiate_boilerplate",
              "Create the agent project: wholesale-copies the tested "
              "boilerplate into this session's workspace. Call ONCE, at the "
              "start of Step 4, with the agent's name.",
              {"project_name": str})
        async def instantiate_boilerplate(args: dict[str, Any]) -> dict[str, Any]:
            return await session.do_instantiate(args)

        @tool("run_selftest",
              "Run the generated project's selftest.py in mock mode. The test is "
              "DOMAIN-AGNOSTIC and FIXED — it derives every check from config.py, "
              "so you NEVER edit it (writes to selftest.py are blocked). Just make "
              "config.py and prompts.py correct. The build is not done until this "
              "reports PASS.",
              {})
        async def run_selftest(args: dict[str, Any]) -> dict[str, Any]:
            return await session.do_run_selftest(args)

        return [instantiate_boilerplate, run_selftest]

    # -- permission callback ---------------------------------------------------

    async def _can_use_tool(self, tool_name: str, input_data: dict[str, Any],
                            context: Any) -> Any:
        if tool_name in ("Write", "Edit", "MultiEdit"):
            target = str(input_data.get("file_path", ""))
            why = write_denial(target, self.project_dir)
            if why is None:
                self.selftest_passed = False  # any edit invalidates the gate
                _clear_pass_marker(self.project_dir)
                return PermissionResultAllow(updated_input=input_data)
            return PermissionResultDeny(message=why)
        if tool_name in ("Read", "Glob", "Grep"):
            target = str(input_data.get("file_path")
                         or input_data.get("path") or "")
            why = read_denial(target, self.workspace_dir)
            if why is None:
                return PermissionResultAllow(updated_input=input_data)
            return PermissionResultDeny(message=why)
        # Anything else that fell through to a prompt is not in the builder's
        # contract — deny loudly rather than guess.
        return PermissionResultDeny(
            message=f"{tool_name} is not available to the builder")

    # -- lifecycle --------------------------------------------------------------

    def _options(self) -> ClaudeAgentOptions:
        server = create_sdk_mcp_server(
            name="platform", version="1.0.0", tools=self._make_platform_tools())
        # Forward the Anthropic key to the CLI subprocess EXPLICITLY when a real
        # one is configured. The subprocess already inherits os.environ, but an
        # explicit options.env entry documents the dependency and guarantees it
        # survives any later os.environ mutation. When no usable key is set we
        # pass nothing, so the CLI's own auth (subscription/login) still works —
        # forwarding an empty string would instead disable that fallback.
        extra_env: dict[str, str] = {}
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if key and not env_bootstrap._looks_like_placeholder(key):
            extra_env["ANTHROPIC_API_KEY"] = key
        return ClaudeAgentOptions(
            cwd=str(REPO_ROOT),
            system_prompt=build_system_prompt(self.project_dir),
            model=BUILDER_MODEL,
            effort=BUILDER_EFFORT,       # clamped to low|medium — thinking is a cost
            max_turns=BUILDER_MAX_TURNS,  # runaway bound per client message
            env=extra_env,
            setting_sources=[],          # hermetic: no filesystem settings bleed
            permission_mode="default",   # everything ungated falls to can_use_tool
            mcp_servers={"platform": server},
            allowed_tools=[              # pre-approved (never hit the callback)
                "TodoWrite",
                "mcp__platform__instantiate_boilerplate",
                "mcp__platform__run_selftest",
            ],
            disallowed_tools=[
                "Bash", "BashOutput", "KillShell", "Task", "Agent",
                "WebSearch", "WebFetch", "NotebookEdit",
                # The client is a browser, not a terminal: the SDK's own
                # question tool would render as a bare tool event and strand
                # the turn. Asking happens ONLY via the alta:ask block.
                "AskUserQuestion",
                # Fetches schemas for OTHER deferred tools (Cron*, SendMessage,
                # MCP resource tools, etc.) — none of which the builder has any
                # legitimate use for; it only burns a turn and a tool-chip.
                "ToolSearch",
            ],
            can_use_tool=self._can_use_tool,
        )

    async def start(self) -> None:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        if self.project_dir is None:
            self.project_dir = discover_project(self.workspace_dir)
        if self.project_dir is not None:
            # selftest_passed is otherwise in-memory only: a lost tab or a
            # server restart would show a proven agent as unverified again.
            self.selftest_passed = has_persisted_pass(self.project_dir)
        _usable, msg = env_bootstrap.anthropic_key_status()
        print(f"[builder] {msg}", flush=True)  # loud: where the tokens bill
        self._client = ClaudeSDKClient(options=self._options())
        await self._client.connect()

    async def send(self, user_text: str) -> AsyncIterator[dict[str, Any]]:
        """One builder turn: yields text chunks and tool events as they arrive,
        ending with a result event."""
        if self._client is None:
            raise RuntimeError("session not started")
        self._selftest_runs = 0   # the run+fix-rerun budget is per message
        await self._client.query(user_text)
        async for message in self._client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield {"type": "text", "text": block.text}
                    elif isinstance(block, ToolUseBlock):
                        yield {"type": "tool", "name": block.name}
            elif isinstance(message, ResultMessage):
                # max_turns is a PER-MESSAGE bound, so exhausting it ends the
                # turn cleanly — no error, no text, the stream just closes and
                # the UI's typing dots stop. A build that ran out mid-way then
                # looks finished when it is not. Say so, and say the fix: the
                # budget resets on the next message, so "continue" resumes with
                # full context rather than restarting the build.
                if getattr(message, "subtype", "") == "error_max_turns":
                    yield {"type": "text", "text": (
                        "\n\nI hit my per-message step limit before finishing this build "
                        "-- the agent is only partly written and its selftest has not run "
                        "yet. Send \"continue\" and I'll pick up exactly where I left off."
                    )}
                yield {
                    "type": "result",
                    "is_error": bool(getattr(message, "is_error", False)),
                    "project_dir": str(self.project_dir) if self.project_dir else None,
                    "selftest_passed": self.selftest_passed,
                }

    async def interrupt(self) -> None:
        """Preempt an in-flight turn: signals the SDK to stop the running
        agent turn (and its `claude` subprocess) NOW, without waiting for it
        to finish. Safe to call when idle — a no-op if no turn is running.
        This is the primitive behind the UI Stop button and the hard
        Disconnect: aborting the browser stream alone never stopped the
        backend turn (it kept spending tokens)."""
        if self._client is not None:
            await self._client.interrupt()

    async def close(self) -> None:
        if self._client is not None:
            await self._client.disconnect()
            self._client = None


def _text(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}
