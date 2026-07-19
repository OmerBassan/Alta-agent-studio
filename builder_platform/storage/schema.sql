-- Alta Builder Platform — Local Storage Schema
-- Engine: SQLite 3  (stdlib, zero dependencies)
-- Created by the platform/storage module; never edited by generated agents.

PRAGMA journal_mode = WAL;          -- safe concurrent reads while the server writes
PRAGMA foreign_keys = ON;

-- ─── Sessions ───────────────────────────────────────────────────────
-- One row per web-chat session.  session_id comes from the frontend
-- (e.g. "web_k3x9m2q7") and is the primary key — no auto-increment.

CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT    PRIMARY KEY,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    last_active  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    active       INTEGER NOT NULL DEFAULT 1   -- 1 = open, 0 = closed / expired
);

-- ─── Built Agents ───────────────────────────────────────────────────
-- One row per agent the builder generates.  A session may produce
-- multiple agents (iterative rebuilds), so (session_id) is NOT unique.

CREATE TABLE IF NOT EXISTS built_agents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL REFERENCES sessions(session_id)
                                    ON DELETE CASCADE,
    agent_name      TEXT    NOT NULL,
    project_path    TEXT    NOT NULL,              -- absolute path to Generated_Agents/…
    system_prompt   TEXT,                          -- the ANSWER-tier system prompt snapshot
    selftest_status TEXT    NOT NULL DEFAULT 'pending',  -- pending | running | passed | failed
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_built_agents_session
    ON built_agents(session_id);
