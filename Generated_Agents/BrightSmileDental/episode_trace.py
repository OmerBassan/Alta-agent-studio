"""Per-conversation trace and effective-configuration fingerprint. Generic —
do not edit per domain (engine file, see ENGINE_FILES in builder_core.py).

Two jobs, both zero-model:

  * config_fingerprint() — a deterministic content hash of the business
    configuration ACTUALLY in effect for this process: the bytes of the domain
    surfaces (config.py, prompts.py, tools.py, knowledge/**) plus every scalar
    setting the loaded config module resolved (which captures env overrides
    such as MAX_TOOL_CALLS_PER_TURN). It changes whenever effective behaviour
    can change, including uncommitted edits — unlike a git revision, which is
    recorded alongside it for context only.

  * TraceWriter — appends one JSON line per turn (the node-by-node trace the
    graph accumulated, the user message and the final reply) under one
    episode correlation id, so a run can be inspected and asserted over
    without a human reading a transcript.

The trace itself is produced inside the graph (graph.py wraps each node); this
module only fingerprints and persists.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Optional

# Domain surfaces that define a business's behaviour. Engine files are
# excluded on purpose: they are byte-identical across agents (drift test), so
# they cannot distinguish one business configuration from another.
DOMAIN_FILES = ("config.py", "prompts.py", "tools.py")
KNOWLEDGE_DIR = "knowledge"
_SCALARS = (str, int, float, bool)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _settings(config_module: ModuleType) -> Dict[str, Any]:
    """Every UPPERCASE scalar the loaded config resolved — env overrides included.
    Non-scalars (Flows, callables, regexes) are covered by the file hash instead,
    because their repr is not stable across processes."""
    return {
        name: getattr(config_module, name)
        for name in sorted(vars(config_module))
        if name.isupper() and isinstance(getattr(config_module, name), _SCALARS)
    }


def config_fingerprint(agent_dir: Path, config_module: ModuleType) -> Dict[str, Any]:
    """Deterministic fingerprint of the effective business configuration.

    Returns {"config_sha256", "files": {relpath: sha256}, "settings_sha256"}.
    A missing domain file is recorded as absent rather than skipped silently,
    so its later appearance also changes the fingerprint.
    """
    agent_dir = Path(agent_dir)
    files: Dict[str, Optional[str]] = {}
    for name in DOMAIN_FILES:
        p = agent_dir / name
        files[name] = _sha256(p.read_bytes()) if p.is_file() else None
    kdir = agent_dir / KNOWLEDGE_DIR
    if kdir.is_dir():
        for p in sorted(kdir.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                files[p.relative_to(agent_dir).as_posix()] = _sha256(p.read_bytes())
    settings_blob = json.dumps(_settings(config_module), sort_keys=True, default=str).encode("utf-8")
    settings_sha = _sha256(settings_blob)
    combined = json.dumps({"files": files, "settings_sha256": settings_sha}, sort_keys=True).encode("utf-8")
    return {"config_sha256": _sha256(combined), "files": files, "settings_sha256": settings_sha}


def git_context(path: Path) -> Dict[str, Any]:
    """Git revision and working-tree status, for context only — never the
    fingerprint. A failure is reported as such, not rendered as a clean tree."""
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True,
                             text=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=path,
                               capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        return {"git_rev": rev, "git_dirty": bool(dirty), "git_error": None}
    except (OSError, subprocess.SubprocessError) as e:
        return {"git_rev": None, "git_dirty": None, "git_error": f"{type(e).__name__}: {e}"}


class TraceWriter:
    """Appends a header line, then one line per turn, to <out_dir>/<episode_id>.jsonl.

    Each line is written with a single write() call; a crash can at worst leave
    a truncated LAST line, never corrupt an earlier one.
    """

    def __init__(self, out_dir: Path, agent_dir: Path, config_module: ModuleType,
                 agent_name: str, thread_id: str, live: bool) -> None:
        self.episode_id = uuid.uuid4().hex
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.out_dir / f"{self.episode_id}.jsonl"
        self.fingerprint = config_fingerprint(agent_dir, config_module)
        self._turn = 0
        self._append({
            "type": "episode_start",
            "agent": agent_name,
            "thread_id": thread_id,
            "live_model": live,
            "config_fingerprint": self.fingerprint,
            **git_context(Path(agent_dir)),
        })

    def _append(self, record: Dict[str, Any]) -> None:
        record = {"episode_id": self.episode_id,
                  "ts": datetime.now(timezone.utc).isoformat(), **record}
        line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line)

    def write_turn(self, user_message: str, state: Dict[str, Any]) -> None:
        self._turn += 1
        self._append({
            "type": "turn",
            "turn": self._turn,
            "config_sha256": self.fingerprint["config_sha256"],
            "user_message": user_message,
            "interrupted": bool(state.get("__interrupt__")),
            "trace": list(state.get("trace") or []),
            "final_response": state.get("final_response", ""),
        })
