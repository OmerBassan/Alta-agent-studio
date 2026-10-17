"""Agent runtimes behind the boundary the platform owns (AD-14).

Each implements ``studio.core.ports.AgentRuntime``: it reads an ``AgentView``
and returns one request from the closed taxonomy. No runtime here can reach the
store, an adapter or a channel (FR41)."""
