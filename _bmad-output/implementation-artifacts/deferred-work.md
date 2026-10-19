- source_spec: `_bmad-output/implementation-artifacts/spec-1-12-credential-free-ci-on-a-clean-checkout.md`
  summary: IMPLEMENTATION-STATE §3.6 row "Pinned dependencies, dev separated: VERIFIED IMPLEMENTED" is false — the root requirements.txt holds pytest beside runtime deps and is the only top-level file.
  evidence: requirements.txt lines "Dev / verification (optional)" + pytest==8.3.4; CI installs that single file. Pre-existing row, not introduced by Story 1.12.
- source_spec: `_bmad-output/implementation-artifacts/spec-1-12-credential-free-ci-on-a-clean-checkout.md`
  summary: `python -m studio scenarios` exits 0 when no `*/scenarios.toml` is found, and test_end_to_end parametrizes from the same glob (skips on empty), so a missing scenario set passes the CI gate.
  evidence: studio/__main__.py:85 (glob) and :112 (returns 0 when nothing failed); studio/tests/test_end_to_end.py:22-28. Pre-existing; CI now relies on that exit code.
- source_spec: `_bmad-output/implementation-artifacts/spec-2-1-pin-source-material.md`
  summary: The specification version hash excludes COMPILER_VERSION, so after a compiler upgrade a registry hit serves a recompilation of the same version to episodes pinned on the old compiler output.
  evidence: studio/spec/loader.py:184-186 hashes spec + schema + source hashes only; Core._entry consults the store snapshot only on a registry miss. Belongs with Story 3.1 (durable immutable versions).
