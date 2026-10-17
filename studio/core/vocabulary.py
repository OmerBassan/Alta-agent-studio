"""The closed vocabularies the Core reports in (FR81, AD-5, AD-18).

Every denial is exactly one of three classifications, and carries one reason
from a closed set. Nothing outside these sets may appear in a denial: a new
reason is a platform change, made here, never a string written at a call site.

Classification rule, applied in one place (``REASON_CLASS``):

* ``business_refusal`` — policy correctly denied: the business's rules, the
  platform's guardrails, or an operator decision said no.
* ``spec_defect`` — the specification led to this: it is silent where the
  Agent needed it to speak (FR48), or it presented something as permitted
  that policy then refused (AD-4). Only these enter the specification backlog.
* ``platform_error`` — something on the platform's side failed; never phrased
  to the requester as a decision.
"""

from __future__ import annotations

from typing import Literal

Classification = Literal["spec_defect", "business_refusal", "platform_error"]

Reason = Literal[
    # request shape
    "malformed_request",
    "undeclared_goal",
    "never_goal",
    "undeclared_fact",
    "invalid_fact_value",
    # capabilities
    "not_granted",
    "wrong_kind",
    "invalid_arguments",
    "arguments_not_established",
    "obligations_outstanding",
    "rule_denied",
    "confirmation_missing",
    "authority_not_established",
    "operator_approval_required",
    "operator_denied",
    "effects_suspended",
    # questions and claims
    "never_ask",
    "provenance_invalid",
    "general_knowledge_disabled",
    "conclusion_forbidden",
    "conclusion_undeclared",
    "action_without_evidence",
    "resolution_invalid",
    "rules_silent",
    "escalation_reason_undeclared",
    "nothing_to_retrieve",
    "awaiting_unnamed",
    # platform
    "adapter_failed",
    "adapter_timeout",
    "adapter_missing",
    "agent_failed",
]

REASON_CLASS: dict[str, Classification] = {
    "malformed_request": "platform_error",
    "undeclared_goal": "business_refusal",
    "never_goal": "business_refusal",
    "undeclared_fact": "business_refusal",
    "invalid_fact_value": "business_refusal",
    "not_granted": "business_refusal",
    "wrong_kind": "business_refusal",
    "invalid_arguments": "business_refusal",
    "arguments_not_established": "business_refusal",
    "obligations_outstanding": "business_refusal",
    "rule_denied": "business_refusal",
    "confirmation_missing": "business_refusal",
    "authority_not_established": "business_refusal",
    "operator_approval_required": "business_refusal",
    "operator_denied": "business_refusal",
    "effects_suspended": "business_refusal",
    "never_ask": "business_refusal",
    "provenance_invalid": "business_refusal",
    "general_knowledge_disabled": "business_refusal",
    "conclusion_forbidden": "business_refusal",
    "conclusion_undeclared": "spec_defect",
    "action_without_evidence": "business_refusal",
    "resolution_invalid": "business_refusal",
    "rules_silent": "spec_defect",
    "escalation_reason_undeclared": "spec_defect",
    "nothing_to_retrieve": "business_refusal",
    "awaiting_unnamed": "business_refusal",
    "adapter_failed": "platform_error",
    "adapter_timeout": "platform_error",
    "adapter_missing": "platform_error",
    "agent_failed": "platform_error",
}

Lifecycle = Literal["active", "pending", "closed"]
"""FR60: exactly three states. Business outcome never lives here (FR67)."""

CloseReason = Literal["resolved", "escalated", "halted", "suspended"]

HaltCause = Literal["guard", "budget_exhausted", "stall", "agent_failed"]
