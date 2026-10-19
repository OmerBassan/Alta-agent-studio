- source_spec: `_bmad-output/implementation-artifacts/spec-1-12-credential-free-ci-on-a-clean-checkout.md`
  summary: IMPLEMENTATION-STATE §3.6 row "Pinned dependencies, dev separated: VERIFIED IMPLEMENTED" is false — the root requirements.txt holds pytest beside runtime deps and is the only top-level file.
  evidence: requirements.txt lines "Dev / verification (optional)" + pytest==8.3.4; CI installs that single file. Pre-existing row, not introduced by Story 1.12.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-12-credential-free-ci-on-a-clean-checkout.md`
  summary: `python -m studio scenarios` exits 0 when no `*/scenarios.toml` is found, and test_end_to_end parametrizes from the same glob (skips on empty), so a missing scenario set passes the CI gate.
  evidence: studio/__main__.py:85 (glob) and :112 (returns 0 when nothing failed); studio/tests/test_end_to_end.py:22-28. Pre-existing; CI now relies on that exit code.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-pin-source-material.md`
  summary: The specification version hash excludes COMPILER_VERSION, so after a compiler upgrade a registry hit serves a recompilation of the same version to episodes pinned on the old compiler output.
  evidence: studio/spec/loader.py:184-186 hashes spec + schema + source hashes only; Core._entry consults the store snapshot only on a registry miss. Belongs with Story 3.1 (durable immutable versions).
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-garden-centre.md`
  summary: A capability's adapter is not checked as connected at startup; a missing adapter surfaces only at the first effect as adapter_missing.
  evidence: studio/spec validation never inspects the Core's adapter map; harness `_effect` returns adapter_missing on first use. The System Frame config rule says to validate at startup. Belongs with the Run surfaces / go-live work (Epics 7-8), where adapters are connected.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-garden-centre.md`
  summary: An operator's approval does not resume the episode it was asked in; the claim is created only when the requester writes again.
  evidence: Core.decide_approval records the grant and evidence but delivers no external event (compare record_expiry, Story 1.10). An approval as an external event would let the Agent act on it. Belongs with Story 7.8 / the approvals surface.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-6-garden-centre.md`
  summary: A finding of fault stated in prose, or quoted from material, without a typed conclusion claim is not caught deterministically.
  evidence: The conclusion gate (`customer_neglect` forbidden) acts on typed claims only; `will_not_say` is prompt text. This is the stated T6 limitation; it is measured in evaluation (NFR6, Epic 4), never claimed as enforced.
