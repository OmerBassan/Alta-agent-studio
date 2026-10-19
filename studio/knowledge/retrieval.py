"""The retrieval port and its lexical default (T10, approved 2026-10-19).

The Core asks a ``Retriever`` for the items of the episode's pinned material
that best match a query; which items exist, and which references they get, stay
the Core's. Lexical matching is the default because sources are short and
measured recall comes first (E-07); an embeddings implementation over
``/v1/embeddings`` can replace it behind this port only if measured misses
justify it.
"""

from __future__ import annotations

import re
from typing import Protocol, Sequence

from studio.spec.compile import ContextItem

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset("a an and are at be can do for how i in is it me my of on or the to we what when you your".split())


def terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP and len(w) > 1}


class Retriever(Protocol):
    def search(self, query: str, items: Sequence[ContextItem], limit: int) -> list[ContextItem]:
        """The best-matching items, best first; empty when nothing matches."""
        ...


class LexicalRetriever:
    """Shared-term overlap; ties go to the higher-authority item, then a stable id."""

    def search(self, query: str, items: Sequence[ContextItem], limit: int) -> list[ContextItem]:
        wanted = terms(query)
        scored = [(len(wanted & terms(i.title + " " + i.text)), i) for i in items]
        ranked = sorted((s for s in scored if s[0]), key=lambda s: (-s[0], s[1].precedence, s[1].item_id))
        return [item for _, item in ranked[:limit]]
