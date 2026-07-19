"""Agentic-RAG SUBGRAPH: an iterative retrieve -> grade -> rewrite loop,
compiled as its own StateGraph and mounted as ONE node of the parent pipeline.
Generic — the corpus/retriever enter via config.py; do not edit per client.

Why a subgraph (and not more parent nodes): the parent graph's contract is a
deterministic, single-pass turn — every path reaches END once, no internal
loops (Same_Turn_Pipeline.txt invariant 3). Multi-hop retrieval genuinely
needs a loop, so the loop is ENCAPSULATED here, behind a private state
namespace, and the parent sees a single node with a single output key.

  RagState (PRIVATE TypedDict — never merged into the parent AgentState)
    retrieve  -> pull top-k docs for the current query (config.RETRIEVER)
    grade     -> are the docs sufficient to answer? (deterministic in mock;
                 cheap INTENT-tier model call in live mode)
    rewrite   -> insufficient: rephrase the query, loop back to retrieve
                 (bounded by config.RAG_MAX_ITERATIONS — the circuit breaker)
    finalize  -> compose the finalized context payload (or "" when nothing
                 relevant was found -> the knowledge node answers honestly)

The parent's agentic_retrieval node (nodes.py) invokes this compiled graph and
copies back EXACTLY ONE key: `retrieved_context`. Documents, grades, and
rewrite counters never leak upward.
"""

from __future__ import annotations

import logging
from typing import List, TypedDict

from langgraph.graph import END, START, StateGraph

import config
import prompts
from llm_client import llm_client, ANSWER_MODEL, INTENT_MODEL

logger = logging.getLogger(__name__)


class RagState(TypedDict, total=False):
    """Private namespace of the retrieval loop. NOT the parent AgentState."""

    query: str            # current (possibly rewritten) search query
    original_query: str   # the user's untouched question
    history_hint: str     # salient conversation terms (parent-composed,
                          # deterministic) so a rewrite can resolve "it"/"that"
    documents: List[dict] # retrieved docs [{"id","title","text","score"}]
    sufficient: bool      # grade verdict for the current documents
    rewrite_count: int    # loop iterations spent (circuit breaker)
    context: str          # finalized payload handed back to the parent


async def retrieve_node(state: RagState) -> dict:
    query = state.get("query", "")
    docs = config.RETRIEVER(query)
    # Confidence floor (report-12 R-05): a below-floor match is dropped BEFORE
    # grading, so low-confidence retrieval degrades to the honest fallback
    # instead of feeding a near-miss chunk to the synthesis prompt. Default 0
    # (off) fits the mock overlap-count retriever; live cosine retrievers
    # typically set ~0.70 via RETRIEVAL_MIN_SCORE.
    if config.RETRIEVAL_MIN_SCORE > 0:
        docs = [d for d in docs if d.get("score", 0) >= config.RETRIEVAL_MIN_SCORE]
    logger.info("rag retrieve %r -> %d docs", query, len(docs))
    return {"documents": docs}


async def grade_node(state: RagState) -> dict:
    """Relevance grade. Mock: score threshold. Live: one cheap INTENT-tier
    yes/no call (degrades to the mock heuristic on any error)."""
    docs = state.get("documents", [])
    if not docs:
        return {"sufficient": False}
    if llm_client.mock:
        return {"sufficient": any(d.get("score", 0) >= 1 for d in docs)}
    try:
        joined = "\n".join(f"- {d['title']}: {d['text']}" for d in docs)
        verdict = await llm_client.generate_text(
            INTENT_MODEL,
            [{"role": "system", "content": prompts.RAG_GRADE_SYSTEM},
             {"role": "user", "content": f"Question: {state.get('original_query', '')}\n\nDocuments:\n{joined}"}],
            temperature=0.0, max_tokens=5,
        )
        return {"sufficient": verdict.strip().lower().startswith("yes")}
    except Exception as e:
        logger.warning("rag grade failed (%s); using score heuristic", type(e).__name__)
        return {"sufficient": any(d.get("score", 0) >= 1 for d in docs)}


async def rewrite_node(state: RagState) -> dict:
    """Rephrase the query for another retrieval pass, HISTORY-AWARE (report-12
    R-03): the parent's deterministic history_hint lets this already-budgeted
    call resolve co-references ("it" -> the actual entity) — the standalone-
    query rewrite happens on a MISS, never as a standing pre-search hop.
    Mock: strip to content words + append unseen hint terms. Live: one
    ANSWER-tier call — the CRAG corrective path. This node only ever runs
    AFTER a miss (a free pre-generation escalation signal), so the stronger
    tier costs nothing on the happy path; grading stays INTENT-tier because
    it runs on every retrieval turn."""
    count = state.get("rewrite_count", 0) + 1
    original = state.get("original_query", state.get("query", ""))
    hint = state.get("history_hint", "")
    fallback = " ".join(w for w in original.lower().split() if w not in config._STOPWORDS)
    if hint:
        low = f"{fallback} {original.lower()}"
        extra = [w for w in hint.split() if w.lower() not in low]
        fallback = f"{fallback} {' '.join(extra)}".strip()
    if llm_client.mock:
        return {"query": fallback or original, "rewrite_count": count}
    try:
        user = (f"Conversation context: {hint}\n\nQuestion: {original}" if hint
                else original)
        rewritten = await llm_client.generate_text(
            ANSWER_MODEL,
            [{"role": "system", "content": prompts.RAG_REWRITE_SYSTEM},
             {"role": "user", "content": user}],
            temperature=0.3, max_tokens=40,
        )
        return {"query": rewritten.strip() or fallback, "rewrite_count": count}
    except Exception as e:
        logger.warning("rag rewrite failed (%s); using keyword fallback", type(e).__name__)
        return {"query": fallback or original, "rewrite_count": count}


async def finalize_node(state: RagState) -> dict:
    """Compose the single payload the parent receives. Empty string = nothing
    relevant found; the knowledge node then answers 'I don't have that' rather
    than hallucinating (Agentic_RAG_Explained.txt rule 4)."""
    if not state.get("sufficient"):
        return {"context": ""}
    docs = state.get("documents", [])
    context = "\n".join(f"[{d['title']}] {d['text']}" for d in docs)
    return {"context": context}


def route_after_grade(state: RagState) -> str:
    """Loop while insufficient AND under the iteration cap; else finalize."""
    if state.get("sufficient"):
        return "finalize"
    if state.get("rewrite_count", 0) >= config.RAG_MAX_ITERATIONS:
        logger.info("rag circuit breaker: %d iterations, finalizing empty",
                    state.get("rewrite_count", 0))
        return "finalize"
    return "rewrite"


def build_rag_subgraph():
    """Compile the private retrieval loop. No checkpointer — the subgraph is
    stateless per invocation; persistence belongs to the parent."""
    b = StateGraph(RagState)
    b.add_node("retrieve", retrieve_node)
    b.add_node("grade", grade_node)
    b.add_node("rewrite", rewrite_node)
    b.add_node("finalize", finalize_node)

    b.add_edge(START, "retrieve")
    b.add_edge("retrieve", "grade")
    b.add_conditional_edges("grade", route_after_grade,
                            {"finalize": "finalize", "rewrite": "rewrite"})
    b.add_edge("rewrite", "retrieve")
    b.add_edge("finalize", END)
    return b.compile()


# Compiled once at import; invoked by nodes.agentic_retrieval_node.
rag_subgraph = build_rag_subgraph()
