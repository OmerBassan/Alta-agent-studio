"""Load a Business Specification from TOML and pin it by content.

The version of a specification is a content hash of its canonical form plus the
content of every source it declares (FR21, FR30). Three consequences:

* the same specification in two folders, or on two machines, has the same
  version — the identity is the content, not the path;
* reordering entries in the file does not change the version, because list
  order carries no meaning (FR18) and the canonical form sorts it away;
* editing a source document changes the version even if the TOML is untouched,
  so two businesses can never differ "because of a revised leaflet" while their
  specifications look identical (FR30).
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from studio.spec.findings import Finding, SpecificationError
from studio.spec.model import BusinessSpecification

SCHEMA_VERSION = "1"

SEQUENCING_KEYS = frozenset({
    "order", "step", "steps", "sequence", "then", "next", "after", "before",
    "first", "flow", "transition", "transitions", "stage", "stages", "workflow",
})
"""Keys that would express ordering. The closed schema already rejects them as
unknown fields; naming them lets the error say *why* (FR24)."""

_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*\S)\s*$")


@dataclass(frozen=True)
class SourceSection:
    locator: str
    heading: str
    text: str


@dataclass(frozen=True)
class SourceDocument:
    id: str
    path: Path
    content_hash: str
    precedence: int
    sections: tuple[SourceSection, ...]


@dataclass(frozen=True)
class LoadedSpecification:
    spec: BusinessSpecification
    version: str
    path: Path
    sources: dict[str, SourceDocument] = field(default_factory=dict)
    load_findings: tuple[Finding, ...] = ()
    """Non-fatal problems found while loading (e.g. an unreadable source), to be
    reported by the validation suite as blocking findings."""

    @property
    def tenant(self) -> str:
        return self.spec.business.tenant


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: Any) -> Any:
    """Order-free canonical form: dicts by key, every list sorted."""
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        items = [_canonical(v) for v in value]
        return sorted(items, key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
    return value


def canonical_json(spec: BusinessSpecification) -> str:
    return json.dumps(_canonical(spec.model_dump(mode="json")), sort_keys=True,
                      ensure_ascii=False, separators=(",", ":"))


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split a source document into addressable sections.

    A Markdown heading starts a section; without headings, each blank-line
    paragraph is a section. Returns ``(heading, body)`` pairs; the locator is
    assigned by position so it is stable for unchanged content."""
    sections: list[tuple[str, list[str]]] = []
    heading = ""
    buffer: list[str] = []
    has_headings = any(_HEADING.match(line) for line in text.splitlines())
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            if any(s.strip() for s in buffer):
                sections.append((heading, buffer))
            heading, buffer = m.group(1), []
            continue
        if not has_headings and not line.strip():
            if any(s.strip() for s in buffer):
                sections.append((heading, buffer))
            buffer = []
            continue
        buffer.append(line)
    if any(s.strip() for s in buffer):
        sections.append((heading, buffer))
    return [(h, "\n".join(b).strip()) for h, b in sections]


def _schema_findings(error: ValidationError) -> list[Finding]:
    findings = []
    for err in error.errors():
        loc = ".".join(str(p) for p in err["loc"])
        last = str(err["loc"][-1]) if err["loc"] else ""
        if err["type"] == "extra_forbidden" and last.lower() in SEQUENCING_KEYS:
            message = (f"'{last}' would express an order of steps, and a specification cannot "
                       "express ordering. Say what must be true before an action as an obligation "
                       "of the goal or an input of the capability instead.")
            code = "sequencing_construct"
        elif err["type"] == "extra_forbidden":
            message = f"'{last}' is not something a specification can contain."
            code = "unknown_field"
        else:
            message = f"{loc}: {err['msg']}"
            code = "schema"
        findings.append(Finding(code=code, severity="blocking", message=message, location=loc))
    return findings


def load_specification(path: str | Path) -> LoadedSpecification:
    """Read, validate the schema of, and pin one specification.

    Raises ``SpecificationError`` (with blocking findings) when the file cannot
    become a specification. A declared source that cannot be read does not
    raise: it is recorded as a load finding, so the validation suite reports it
    and nothing from it is used (FR117, UX "Could not be read").
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise SpecificationError([Finding(code="unreadable", severity="blocking",
                                          message=f"The specification file could not be read: {exc}")]) from exc
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise SpecificationError([Finding(code="not_toml", severity="blocking",
                                          message=f"The specification is not valid TOML: {exc}")]) from exc
    try:
        spec = BusinessSpecification.model_validate(data)
    except ValidationError as exc:
        raise SpecificationError(_schema_findings(exc)) from exc

    sources: dict[str, SourceDocument] = {}
    load_findings: list[Finding] = []
    for source in (spec.grounding.sources if spec.grounding else ()):
        source_path = (path.parent / source.path).resolve()
        try:
            content = source_path.read_bytes()
            text = content.decode("utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            load_findings.append(Finding(
                code="source_unreadable", severity="blocking", area="EX14",
                location=f"grounding.sources.{source.id}",
                message=f"Source '{source.id}' could not be read. Nothing from it has been used. ({exc})"))
            continue
        sections = tuple(
            SourceSection(locator=f"{source.id}#{i + 1}", heading=h, text=t)
            for i, (h, t) in enumerate(split_sections(text))
        )
        sources[source.id] = SourceDocument(id=source.id, path=source_path, content_hash=_sha256(content),
                                            precedence=source.precedence, sections=sections)

    pinned = canonical_json(spec) + "|schema=" + SCHEMA_VERSION + "|" + "|".join(
        f"{sid}={doc.content_hash}" for sid, doc in sorted(sources.items()))
    return LoadedSpecification(spec=spec, version=_sha256(pinned.encode("utf-8"))[:16], path=path,
                               sources=sources, load_findings=tuple(load_findings))
