"""Typed validation findings — the shape every specification check reports in.

A finding is either *blocking* (the specification cannot be promoted or
deployed: FR22) or a *warning* (shown, never blocking). Messages are written for
the person who owns the specification: plain language, naming what to change.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

Severity = Literal["blocking", "warning"]


class Finding(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    severity: Severity
    message: str
    area: Optional[str] = None
    """Expression area (EX1–EX17) the finding concerns, so a surface can point at
    the part of the specification it is about (UX Amendment 13)."""
    location: Optional[str] = None
    """Path inside the specification, e.g. ``capabilities.book_visit.inputs``."""


class SpecificationError(Exception):
    """The file could not be turned into a specification at all (unreadable,
    not TOML, or not matching the schema). Carries blocking findings so the
    failure is a stated outcome, never a silent one (FR117)."""

    def __init__(self, findings: list[Finding]):
        self.findings = findings
        super().__init__("; ".join(f.message for f in findings))
