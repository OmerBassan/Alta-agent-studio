"""Per-turn trace and effective-configuration fingerprint (C5).

Proven against boilerplate/'s own config in mock mode, like the other engine
invariants. The fingerprint tests use a copy of the domain surfaces in a temp
directory so they can edit files without touching the repository — which is
exactly the uncommitted-edit case a git revision cannot see.
"""

import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

os.environ["OPENAI_API_KEY"] = ""
os.environ["OPENAI_BASE_URL"] = ""

BOILERPLATE_DIR = Path(__file__).resolve().parents[2] / "boilerplate"
sys.path.insert(0, str(BOILERPLATE_DIR))

import config  # noqa: E402
from episode_trace import DOMAIN_FILES, TraceWriter, config_fingerprint  # noqa: E402
from graph import TURN_RESET, build_pipeline  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from schemas import append_or_reset  # noqa: E402

BOOK = "I'd like to book a fitting at the downtown branch tomorrow at 3pm"


@pytest.fixture
def agent_copy(tmp_path: Path) -> Path:
    for name in (*DOMAIN_FILES, "nodes.py"):
        shutil.copy(BOILERPLATE_DIR / name, tmp_path / name)
    return tmp_path


async def _turn(graph, cfg, text):
    payload = dict(TURN_RESET)
    payload["user_message"] = text
    payload["recent_messages"] = [HumanMessage(content=text)]
    return await graph.ainvoke(payload, config=cfg)


# --- reducer ---------------------------------------------------------------

def test_append_or_reset_semantics():
    assert append_or_reset([{"a": 1}], [{"b": 2}]) == [{"a": 1}, {"b": 2}]
    assert append_or_reset([{"a": 1}], []) == []          # empty list = new turn
    assert append_or_reset([{"a": 1}], None) == [{"a": 1}]
    assert append_or_reset(None, [{"b": 2}]) == [{"b": 2}]


# --- fingerprint -------------------------------------------------------------

def test_fingerprint_is_deterministic(agent_copy):
    assert config_fingerprint(agent_copy, config) == config_fingerprint(agent_copy, config)


def test_fingerprint_changes_on_uncommitted_domain_edit(agent_copy):
    before = config_fingerprint(agent_copy, config)["config_sha256"]
    with (agent_copy / "config.py").open("a", encoding="utf-8") as f:
        f.write("\n# operator correction, not yet committed\n")
    after = config_fingerprint(agent_copy, config)["config_sha256"]
    assert before != after


def test_fingerprint_changes_on_effective_setting(agent_copy, monkeypatch):
    # Env-derived knobs are resolved into module attributes at import; a change
    # there changes behaviour without touching any file, so it must count too.
    before = config_fingerprint(agent_copy, config)
    monkeypatch.setattr(config, "MAX_TOOL_CALLS_PER_TURN", config.MAX_TOOL_CALLS_PER_TURN + 1)
    after = config_fingerprint(agent_copy, config)
    assert before["settings_sha256"] != after["settings_sha256"]
    assert before["config_sha256"] != after["config_sha256"]


def test_fingerprint_changes_when_knowledge_is_added(agent_copy):
    before = config_fingerprint(agent_copy, config)["config_sha256"]
    (agent_copy / "knowledge").mkdir()
    (agent_copy / "knowledge" / "returns.md").write_text("Returns within 30 days.", encoding="utf-8")
    after = config_fingerprint(agent_copy, config)
    assert after["config_sha256"] != before
    assert "knowledge/returns.md" in after["files"]


def test_fingerprint_ignores_engine_files(agent_copy):
    # Engine files are byte-identical across agents (drift test), so they must
    # not make two runs of the same business configuration look different.
    before = config_fingerprint(agent_copy, config)["config_sha256"]
    with (agent_copy / "nodes.py").open("a", encoding="utf-8") as f:
        f.write("\n# engine edit\n")
    assert config_fingerprint(agent_copy, config)["config_sha256"] == before


# --- trace through a real mock-mode run -------------------------------------

def test_trace_records_decisions_and_resets_each_turn():
    async def run():
        graph = build_pipeline(MemorySaver())
        cfg = {"configurable": {"thread_id": "trace-booking"}}
        return await _turn(graph, cfg, BOOK), await _turn(graph, cfg, "yes")

    first, second = asyncio.run(run())
    t1 = {e["node"]: e for e in first["trace"]}
    assert t1["intent_detect"]["intent"] == "book_fitting"
    assert t1["think"]["tool"] == "book_appointment"
    assert t1["think"]["awaiting_confirmation"] is True and t1["think"]["act"] is False
    assert "tool_exec" not in t1                      # nothing ran before the customer said yes

    nodes_2 = [e["node"] for e in second["trace"]]
    assert nodes_2.count("intent_detect") == 1        # turn 1's entries were reset, not carried
    t2 = {e["node"]: e for e in second["trace"]}
    assert t2["intent_detect"]["confirmed_action"] == "book_appointment"
    assert t2["tool_exec"]["tool"] == "book_appointment" and t2["tool_exec"]["ok"] is True
    assert t2["execution_validator"]["ok"] is True
    assert nodes_2[-1] == "validator"
    assert second["trace"][-1]["final_response"] == second["final_response"]


def test_trace_writer_persists_header_and_turns(tmp_path):
    async def run():
        graph = build_pipeline(MemorySaver())
        cfg = {"configurable": {"thread_id": "trace-writer"}}
        writer = TraceWriter(out_dir=tmp_path / "traces", agent_dir=BOILERPLATE_DIR,
                             config_module=config, agent_name=config.AGENT_NAME,
                             thread_id="trace-writer", live=False)
        for text in (BOOK, "yes"):
            writer.write_turn(text, await _turn(graph, cfg, text))
        return writer

    writer = asyncio.run(run())
    lines = [json.loads(line) for line in writer.path.read_text(encoding="utf-8").splitlines()]
    assert [r["type"] for r in lines] == ["episode_start", "turn", "turn"]
    assert {r["episode_id"] for r in lines} == {writer.episode_id}   # one correlation id
    header = lines[0]
    assert header["config_fingerprint"]["config_sha256"] == writer.fingerprint["config_sha256"]
    assert "git_rev" in header and "git_dirty" in header
    assert all(r["config_sha256"] == writer.fingerprint["config_sha256"] for r in lines[1:])
    assert lines[2]["trace"][-1]["node"] == "validator"
