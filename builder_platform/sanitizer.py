"""Pre-TTS text sanitizer — adapter-side, buffered (Day 1 PM).

Why buffered and stateful, not a per-chunk pure function: markdown tokens can
split across chunk boundaries (``**bo`` + ``ld**``), and a URL split across two
chunks would dodge the URL regex. The sanitizer therefore holds the trailing
partial word in a buffer and only releases text up to the last whitespace
boundary; ``flush()`` releases the remainder at end-of-stream.

What it strips (things a TTS voice would read aloud as garbage):
- markdown emphasis/heading/code characters  ``* _ # ` ~ [ ] ( )``
- bullet markers at line starts (``- item`` / ``• item``)
- URLs -> the spoken word "link"
- newlines and runs of whitespace -> a single space

This is the platform backstop. The in-graph validator + BLOCKED_PATTERNS keep
covering domain rules, and generated agents are styled for speech at design
time — text that needs sanitizing is a defect, but it must never reach the ear.
"""

from __future__ import annotations

import re

_URL = re.compile(r"https?://\S+|www\.\S+")
_BULLET = re.compile(r"(?m)^[ \t]*[-•*]\s+")
_MARKDOWN = re.compile(r"[*_#`~\[\]()]")
_WS = re.compile(r"\s+")
# Last safe release point: the final whitespace char in the buffer. Everything
# after it may be a partial word/URL/markdown token still being streamed.
_LAST_WS = re.compile(r"\s(?=\S*$)")


def _clean(text: str) -> str:
    text = _URL.sub(" link ", text)
    text = _BULLET.sub(" ", text)
    text = _MARKDOWN.sub(" ", text)
    return _WS.sub(" ", text)


class StreamSanitizer:
    """Feed chunks with ``process_chunk``; call ``flush`` after the last one."""

    def __init__(self) -> None:
        self._buffer = ""

    def process_chunk(self, chunk: str) -> str:
        self._buffer += chunk
        m = None
        for m in _LAST_WS.finditer(self._buffer):
            pass  # keep the LAST whitespace match
        if m is None:
            return ""  # no boundary yet — keep buffering
        release, self._buffer = self._buffer[: m.end()], self._buffer[m.end():]
        return _clean(release)

    def flush(self) -> str:
        release, self._buffer = self._buffer, ""
        return _clean(release) if release else ""


def sanitize_text(text: str) -> str:
    """One-shot sanitize for text that is already complete (e.g. the graph's
    final_response, which arrives whole). Same rules as the streaming path."""
    s = StreamSanitizer()
    return (s.process_chunk(text) + s.flush()).strip()


def sentence_chunks(text: str) -> list[str]:
    """Split into sentence-sized chunks so TTS can start on the first one."""
    out: list[str] = []
    buf: list[str] = []
    for word in text.split():
        buf.append(word)
        if word.endswith((".", "?", "!")):
            out.append(" ".join(buf))
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out
