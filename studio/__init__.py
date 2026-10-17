"""Agent Studio — the business-specific agent platform (V1).

A Business Specification (``studio.spec``) is compiled by the Core
(``studio.core``) into three projections: the Agent's context, the capability
surface offered to the model, and the policy the Core enforces. The Agent
(``studio.agent``) decides what to do next; the Core decides what the Agent is
permitted to do, executes it through adapters (``studio.extensions``), and
records what happened. Architecture: ARCHITECTURE-SPINE.md (AD-1 … AD-25).

This package is the new product line. The shipped voice builder
(``boilerplate/``, ``builder_platform/``, ``Generated_Agents/``) is a separate
product with its own spec of record and is not imported here.
"""
