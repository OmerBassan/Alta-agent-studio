"""Pure policy functions: argument canonicalisation, the closed predicate
language, payload digests and idempotency keys.

No I/O, no state: each function answers one question about a request against
the compiled policy, so every check can be tested in isolation.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any, Iterable, Optional

from studio.core.types import Argument
from studio.spec.compile import CapabilityPolicy, DenyRule, PredicatePolicy

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class ArgumentError(ValueError):
    pass


def coerce(type_: str, value: Any) -> Any:
    """Validate one value against a declared type; return it in canonical form.

    Model output is untrusted input: strings that spell a number are accepted
    for numeric types, everything else must already be the right shape."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ArgumentError("is empty")
    if type_ == "string":
        if isinstance(value, bool) or not isinstance(value, (str, int, float)):
            raise ArgumentError("must be text")
        return str(value).strip()
    if type_ == "integer":
        if isinstance(value, bool):
            raise ArgumentError("must be a whole number")
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ArgumentError("must be a whole number") from None
        if number != int(number):
            raise ArgumentError("must be a whole number")
        return int(number)
    if type_ == "number":
        if isinstance(value, bool):
            raise ArgumentError("must be a number")
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ArgumentError("must be a number") from None
    if type_ == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.lower() in ("true", "false"):
            return value.lower() == "true"
        raise ArgumentError("must be true or false")
    if type_ == "date":
        text = str(value).strip()
        if not _DATE.match(text):
            raise ArgumentError("must be a date written YYYY-MM-DD")
        try:
            date.fromisoformat(text)
        except ValueError:
            raise ArgumentError("is not a real date") from None
        return text
    if type_ == "time":
        text = str(value).strip()
        if not _TIME.match(text):
            raise ArgumentError("must be a time written HH:MM")
        return text
    raise ArgumentError(f"has unknown type {type_}")


def canonical_arguments(cap: CapabilityPolicy, arguments: Iterable[Argument]) -> dict[str, Any]:
    """Validate a request's arguments against the capability contract.

    Unknown names, duplicates, missing required inputs and ill-typed values
    are all refused; the result is the canonical payload the Core binds gates
    and idempotency keys to."""
    declared = {i.name: i for i in cap.inputs}
    out: dict[str, Any] = {}
    for arg in arguments:
        if arg.name not in declared:
            raise ArgumentError(f"'{arg.name}' is not an input of {cap.name}")
        if arg.name in out:
            raise ArgumentError(f"'{arg.name}' is given twice")
        try:
            out[arg.name] = coerce(declared[arg.name].type, arg.value)
        except ArgumentError as exc:
            raise ArgumentError(f"'{arg.name}' {exc}") from None
    missing = [name for name, i in declared.items() if i.required and name not in out]
    if missing:
        raise ArgumentError(f"missing required input(s): {', '.join(missing)}")
    return out


def _compare(op: str, actual: Any, expected: Any) -> bool:
    if isinstance(actual, (int, float)) and not isinstance(expected, (int, float)):
        try:
            expected = float(expected)
        except (TypeError, ValueError):
            return False
    try:
        if op == "lt":
            return actual < expected
        if op == "le":
            return actual <= expected
        if op == "gt":
            return actual > expected
        if op == "ge":
            return actual >= expected
    except TypeError:
        return False
    raise ValueError(op)


def predicate_holds(predicate: PredicatePolicy, values: dict[str, Any]) -> bool:
    """Evaluate one predicate over the known values. A predicate about a value
    that is not known does not hold — except ``absent``."""
    present = predicate.fact in values and values[predicate.fact] not in (None, "")
    if predicate.op == "present":
        return present
    if predicate.op == "absent":
        return not present
    if not present:
        return False
    actual = values[predicate.fact]
    expected = predicate.value
    if predicate.op == "eq":
        return str(actual).lower() == str(expected).lower()
    if predicate.op == "ne":
        return str(actual).lower() != str(expected).lower()
    if predicate.op in ("in", "not_in"):
        options = {str(v).lower() for v in (expected or ())}
        inside = str(actual).lower() in options
        return inside if predicate.op == "in" else not inside
    if predicate.op == "weekday_in":
        try:
            weekday = _WEEKDAYS[date.fromisoformat(str(actual)).weekday()]
        except ValueError:
            return False
        return weekday in {str(v).lower() for v in (expected or ())}
    return _compare(predicate.op, actual, expected)


def denying_rule(rules: Iterable[DenyRule], values: dict[str, Any]) -> Optional[DenyRule]:
    """The first rule (by id) whose every predicate holds, or None."""
    for rule in rules:
        if rule.always or (rule.predicates and all(predicate_holds(p, values) for p in rule.predicates)):
            return rule
    return None


def _hash(*parts: Any) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def payload_digest(tenant: str, episode_id: str, spec_version: str, capability: str, arguments: dict) -> str:
    """What a confirmation or approval is bound to: this tenant, this episode,
    this specification version, this capability, these exact arguments. Any
    difference is a different digest, so no record can be reused for another
    payload, conversation or version (DL-008)."""
    return _hash(tenant, episode_id, spec_version, capability, arguments)[:32]


def idempotency_key(tenant: str, episode_id: str, capability: str, arguments: dict) -> str:
    """Core-issued, scoped by tenant and episode (AD-10). The same payload in
    the same episode is the same effect; the same payload elsewhere is not."""
    return "idem_" + _hash("idempotency", tenant, episode_id, capability, arguments)[:24]
