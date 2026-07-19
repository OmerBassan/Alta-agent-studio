"""Pre-TTS sanitizer regression tests.

The load-bearing property: markdown tokens and URLs SPLIT ACROSS CHUNK
BOUNDARIES must still be stripped — a per-chunk pure function cannot do this
(the reason the sanitizer is stateful and buffered).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sanitizer import StreamSanitizer, sanitize_text, sentence_chunks  # noqa: E402


def _run_chunks(chunks):
    s = StreamSanitizer()
    out = "".join(s.process_chunk(c) for c in chunks) + s.flush()
    return out


def test_markdown_split_across_chunks():
    assert "*" not in _run_chunks(["**bo", "ld** text"])
    assert "bo" in _run_chunks(["**bo", "ld** text"])


def test_url_split_across_chunks_becomes_link():
    out = _run_chunks(["see https://exa", "mple.com/a?b=1 for details"])
    assert "http" not in out
    assert " link " in out


def test_partial_word_not_released_early():
    s = StreamSanitizer()
    assert s.process_chunk("Hello wor") == "Hello "
    assert s.process_chunk("ld! Bye") == "world! "
    assert s.flush() == "Bye"


def test_bullets_and_headers_stripped():
    out = sanitize_text("# Plans\n- Basic: $9\n- Pro: $29")
    assert "#" not in out and "-" not in out
    assert "Basic: $9" in out


def test_whitespace_collapsed_no_newlines():
    out = sanitize_text("line one\n\nline   two")
    assert "\n" not in out and "  " not in out


def test_clean_text_passes_through():
    text = "Hi there. Can I get your email?"
    assert sanitize_text(text) == text


def test_sentence_chunks():
    assert sentence_chunks("One. Two? Three") == ["One.", "Two?", "Three"]
    assert sentence_chunks("") == []
