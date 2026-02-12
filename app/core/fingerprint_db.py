"""
H.I.V.E. Scammer Fingerprint Database
SQLite-backed scammer profiling, cross-referencing, and threat scoring.
"""
import sqlite3
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hive_fingerprints.db")


def _get_conn() -> sqlite3.Connection:
    """Get a connection to the fingerprint database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS scammers (
            id              TEXT PRIMARY KEY,          -- SHA-256 fingerprint
            first_seen      TEXT NOT NULL,
            last_seen       TEXT NOT NULL,
            encounter_count INTEGER DEFAULT 1,
            scam_types      TEXT DEFAULT '[]',         -- JSON array
            threat_score    REAL DEFAULT 0.0,
            status          TEXT DEFAULT 'active',     -- active | flagged | reported
            notes           TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS identifiers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            scammer_id  TEXT NOT NULL,
            type        TEXT NOT NULL,                 -- phone | upi | bank_account | link | chat_id
            value       TEXT NOT NULL,
            first_seen  TEXT NOT NULL,
            FOREIGN KEY (scammer_id) REFERENCES scammers(id),
            UNIQUE(type, value)                        -- each identifier is globally unique
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            scammer_id      TEXT NOT NULL,
            chat_id         TEXT,
            scam_type       TEXT,
            started_at      TEXT NOT NULL,
            last_activity   TEXT NOT NULL,
            message_count   INTEGER DEFAULT 0,
            intel_snapshot   TEXT DEFAULT '{}',         -- JSON of extracted intel at session end
            FOREIGN KEY (scammer_id) REFERENCES scammers(id)
        );

        CREATE INDEX IF NOT EXISTS idx_identifiers_value ON identifiers(value);
        CREATE INDEX IF NOT EXISTS idx_identifiers_scammer ON identifiers(scammer_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_scammer ON sessions(scammer_id);
    """)
    conn.commit()
    conn.close()


# ───────────────────────────────────────────────
# Fingerprint generation
# ───────────────────────────────────────────────

def _generate_fingerprint(identifiers: list[str]) -> str:
    """Generate a deterministic SHA-256 fingerprint from sorted identifiers."""
    normalized = sorted(set(v.strip().lower() for v in identifiers if v.strip()))
    raw = "|".join(normalized)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ───────────────────────────────────────────────
# Core operations
# ───────────────────────────────────────────────

def find_scammer_by_identifier(identifier_value: str) -> Optional[dict]:
    """Look up a scammer by any known identifier (phone, UPI, bank account, etc.)."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT scammer_id FROM identifiers WHERE LOWER(value) = LOWER(?)",
        (identifier_value,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    scammer = _load_scammer(conn, row["scammer_id"])
    conn.close()
    return scammer


def _load_scammer(conn: sqlite3.Connection, scammer_id: str) -> dict:
    """Load full scammer profile including all identifiers and session count."""
    row = conn.execute("SELECT * FROM scammers WHERE id = ?", (scammer_id,)).fetchone()
    if not row:
        return None

    identifiers = conn.execute(
        "SELECT type, value, first_seen FROM identifiers WHERE scammer_id = ?",
        (scammer_id,)
    ).fetchall()

    session_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM sessions WHERE scammer_id = ?",
        (scammer_id,)
    ).fetchone()["cnt"]

    return {
        "fingerprint": row["id"],
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "encounter_count": row["encounter_count"],
        "scam_types": json.loads(row["scam_types"]),
        "threat_score": row["threat_score"],
        "status": row["status"],
        "notes": row["notes"],
        "session_count": session_count,
        "identifiers": [
            {"type": i["type"], "value": i["value"], "first_seen": i["first_seen"]}
            for i in identifiers
        ],
    }


def store_fingerprint(
    intel: dict,
    scam_type: str = "unknown",
    chat_id: str = None,
    message_count: int = 0,
) -> dict:
    """
    Store extracted intelligence and create/update a scammer fingerprint.

    intel: output from extract_all_intelligence() —
           { upiIds, phoneNumbers, bankAccounts, phishingLinks, suspiciousKeywords }

    Returns the scammer profile (new or updated).
    """
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_conn()

    # Collect all identifiers from intel
    id_pairs = []  # (type, value)
    for upi in intel.get("upiIds", []):
        id_pairs.append(("upi", upi))
    for phone in intel.get("phoneNumbers", []):
        id_pairs.append(("phone", phone))
    for acct in intel.get("bankAccounts", []):
        id_pairs.append(("bank_account", acct))
    for link in intel.get("phishingLinks", []):
        id_pairs.append(("link", link))
    if chat_id:
        id_pairs.append(("chat_id", chat_id))

    if not id_pairs:
        conn.close()
        return {"status": "no_identifiers", "message": "No identifiers found to fingerprint."}

    # Check if any identifier already maps to an existing scammer
    existing_scammer_id = None
    for _, value in id_pairs:
        row = conn.execute(
            "SELECT scammer_id FROM identifiers WHERE LOWER(value) = LOWER(?)",
            (value,)
        ).fetchone()
        if row:
            existing_scammer_id = row["scammer_id"]
            break

    if existing_scammer_id:
        # ── Update existing scammer ──
        scammer_id = existing_scammer_id

        # Update last_seen and encounter count
        scammer_row = conn.execute("SELECT * FROM scammers WHERE id = ?", (scammer_id,)).fetchone()
        existing_types = json.loads(scammer_row["scam_types"])
        if scam_type and scam_type not in existing_types:
            existing_types.append(scam_type)

        new_score = _calculate_threat_score(
            encounter_count=scammer_row["encounter_count"] + 1,
            scam_types=existing_types,
            identifier_count=len(id_pairs),
        )

        conn.execute(
            """UPDATE scammers
               SET last_seen = ?, encounter_count = encounter_count + 1,
                   scam_types = ?, threat_score = ?
               WHERE id = ?""",
            (now, json.dumps(existing_types), new_score, scammer_id),
        )

        # Add any new identifiers
        for id_type, id_value in id_pairs:
            try:
                conn.execute(
                    "INSERT INTO identifiers (scammer_id, type, value, first_seen) VALUES (?, ?, ?, ?)",
                    (scammer_id, id_type, id_value, now),
                )
            except sqlite3.IntegrityError:
                pass  # Already exists

        is_new = False
    else:
        # ── Create new scammer ──
        all_values = [v for _, v in id_pairs]
        scammer_id = _generate_fingerprint(all_values)

        types_list = [scam_type] if scam_type else []
        score = _calculate_threat_score(
            encounter_count=1,
            scam_types=types_list,
            identifier_count=len(id_pairs),
        )

        conn.execute(
            """INSERT INTO scammers (id, first_seen, last_seen, encounter_count, scam_types, threat_score)
               VALUES (?, ?, ?, 1, ?, ?)""",
            (scammer_id, now, now, json.dumps(types_list), score),
        )

        for id_type, id_value in id_pairs:
            try:
                conn.execute(
                    "INSERT INTO identifiers (scammer_id, type, value, first_seen) VALUES (?, ?, ?, ?)",
                    (scammer_id, id_type, id_value, now),
                )
            except sqlite3.IntegrityError:
                pass

        is_new = True

    # ── Log session ──
    conn.execute(
        """INSERT INTO sessions (scammer_id, chat_id, scam_type, started_at, last_activity, message_count, intel_snapshot)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (scammer_id, chat_id, scam_type, now, now, message_count, json.dumps(intel)),
    )

    conn.commit()

    # Load and return full profile
    profile = _load_scammer(conn, scammer_id)
    profile["is_new_scammer"] = is_new
    conn.close()
    return profile


# ───────────────────────────────────────────────
# Threat score calculation
# ───────────────────────────────────────────────

def _calculate_threat_score(encounter_count: int, scam_types: list, identifier_count: int) -> float:
    """
    Calculate a 0-100 threat score based on:
    - encounter_count: more encounters = higher threat
    - scam_types: using multiple scam types = more sophisticated
    - identifier_count: more identifiers revealed = more intel gathered
    """
    # Base: encounters (max 40 pts)
    encounter_score = min(encounter_count * 8, 40)

    # Diversity: scam types used (max 30 pts)
    type_score = min(len(scam_types) * 10, 30)

    # Identity exposure: identifiers collected (max 30 pts)
    identity_score = min(identifier_count * 5, 30)

    return round(encounter_score + type_score + identity_score, 1)


# ───────────────────────────────────────────────
# Query helpers
# ───────────────────────────────────────────────

def get_all_scammers(limit: int = 50) -> list[dict]:
    """Return all scammer profiles, ordered by threat score descending."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id FROM scammers ORDER BY threat_score DESC LIMIT ?", (limit,)
    ).fetchall()
    scammers = [_load_scammer(conn, r["id"]) for r in rows]
    conn.close()
    return scammers


def get_scammer_by_fingerprint(fingerprint: str) -> Optional[dict]:
    """Load a scammer profile by their fingerprint ID."""
    conn = _get_conn()
    profile = _load_scammer(conn, fingerprint)
    conn.close()
    return profile


def get_stats() -> dict:
    """Dashboard statistics."""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) as c FROM scammers").fetchone()["c"]
    active = conn.execute("SELECT COUNT(*) as c FROM scammers WHERE status='active'").fetchone()["c"]
    flagged = conn.execute("SELECT COUNT(*) as c FROM scammers WHERE status='flagged'").fetchone()["c"]
    reported = conn.execute("SELECT COUNT(*) as c FROM scammers WHERE status='reported'").fetchone()["c"]

    total_sessions = conn.execute("SELECT COUNT(*) as c FROM sessions").fetchone()["c"]
    total_identifiers = conn.execute("SELECT COUNT(*) as c FROM identifiers").fetchone()["c"]

    top_threat = conn.execute(
        "SELECT id, threat_score FROM scammers ORDER BY threat_score DESC LIMIT 1"
    ).fetchone()

    # Identifier breakdown
    id_breakdown = {}
    for row in conn.execute("SELECT type, COUNT(*) as c FROM identifiers GROUP BY type").fetchall():
        id_breakdown[row["type"]] = row["c"]

    # Scam type distribution
    all_types = []
    for row in conn.execute("SELECT scam_types FROM scammers").fetchall():
        all_types.extend(json.loads(row["scam_types"]))
    type_dist = {}
    for t in all_types:
        type_dist[t] = type_dist.get(t, 0) + 1

    conn.close()
    return {
        "total_scammers": total,
        "active": active,
        "flagged": flagged,
        "reported": reported,
        "total_sessions": total_sessions,
        "total_identifiers": total_identifiers,
        "identifier_breakdown": id_breakdown,
        "scam_type_distribution": type_dist,
        "highest_threat": {
            "fingerprint": top_threat["id"],
            "score": top_threat["threat_score"],
        } if top_threat else None,
    }


def update_scammer_status(fingerprint: str, status: str, notes: str = "") -> bool:
    """Update scammer status to 'active', 'flagged', or 'reported'."""
    if status not in ("active", "flagged", "reported"):
        return False
    conn = _get_conn()
    cur = conn.execute(
        "UPDATE scammers SET status = ?, notes = ? WHERE id = ?",
        (status, notes, fingerprint),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def search_scammers(query: str) -> list[dict]:
    """Search scammers by any identifier value (partial match)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT scammer_id FROM identifiers WHERE LOWER(value) LIKE LOWER(?)",
        (f"%{query}%",)
    ).fetchall()
    results = [_load_scammer(conn, r["scammer_id"]) for r in rows]
    conn.close()
    return results


def merge_scammers(fingerprint_a: str, fingerprint_b: str) -> Optional[dict]:
    """
    Merge two scammer profiles when they are discovered to be the same person.
    All identifiers and sessions from B are moved to A. B is deleted.
    """
    conn = _get_conn()
    a = conn.execute("SELECT * FROM scammers WHERE id = ?", (fingerprint_a,)).fetchone()
    b = conn.execute("SELECT * FROM scammers WHERE id = ?", (fingerprint_b,)).fetchone()
    if not a or not b:
        conn.close()
        return None

    # Merge scam types
    types_a = json.loads(a["scam_types"])
    types_b = json.loads(b["scam_types"])
    merged_types = list(set(types_a + types_b))

    # Move identifiers from B to A
    conn.execute("UPDATE identifiers SET scammer_id = ? WHERE scammer_id = ?", (fingerprint_a, fingerprint_b))
    # Move sessions from B to A
    conn.execute("UPDATE sessions SET scammer_id = ? WHERE scammer_id = ?", (fingerprint_a, fingerprint_b))

    # Update A with merged data
    total_encounters = a["encounter_count"] + b["encounter_count"]
    first_seen = min(a["first_seen"], b["first_seen"])

    id_count = conn.execute(
        "SELECT COUNT(*) as c FROM identifiers WHERE scammer_id = ?", (fingerprint_a,)
    ).fetchone()["c"]

    new_score = _calculate_threat_score(total_encounters, merged_types, id_count)

    conn.execute(
        """UPDATE scammers SET first_seen = ?, encounter_count = ?,
           scam_types = ?, threat_score = ? WHERE id = ?""",
        (first_seen, total_encounters, json.dumps(merged_types), new_score, fingerprint_a),
    )

    # Delete B
    conn.execute("DELETE FROM scammers WHERE id = ?", (fingerprint_b,))

    conn.commit()
    profile = _load_scammer(conn, fingerprint_a)
    conn.close()
    return profile


# Initialize DB on import
init_db()
