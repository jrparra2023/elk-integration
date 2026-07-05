#!/usr/bin/env python3
"""
SentinelCore → ELK — sync.py
Continuous sync mode: polls SentinelCore SQLite every N seconds
and forwards only new events/alerts to Elasticsearch.

Usage
-----
python3 sync.py                  # default: poll every 30s
python3 sync.py --interval 10    # poll every 10s
python3 sync.py --once           # single run and exit
"""

import sys
import time
import json
import argparse
import sqlite3
from pathlib import Path
from datetime import datetime
from elasticsearch import Elasticsearch

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH    = Path.home() / "sentinelcore/logs/sentinelcore.db"
ES_HOST    = "http://localhost:9200"
IDX_EVENTS = "sentinelcore-events"
IDX_ALERTS = "sentinelcore-alerts"
STATE_FILE = Path(__file__).parent / ".sync_state.json"

es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])


# ── State management ──────────────────────────────────────────────────────────

def load_state() -> dict:
    """Load last synced IDs from state file."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_event_id": 0, "last_alert_id": 0}


def save_state(state: dict):
    """Persist last synced IDs."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_new_events(since_id: int) -> list[dict]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM events WHERE id > ? ORDER BY id ASC", (since_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_new_alerts(since_id: int) -> list[dict]:
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM alerts WHERE id > ? ORDER BY id ASC", (since_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Forwarder ─────────────────────────────────────────────────────────────────

def forward_batch(records: list[dict], index: str, is_alert: bool = False) -> tuple[int, int]:
    ok = err = 0
    for r in records:
        doc = {k: v for k, v in r.items() if v is not None and v != ""}
        ts_field = "created_at" if is_alert else "timestamp"
        if ts_field in doc:
            doc["@timestamp"] = doc[ts_field]
        if is_alert:
            doc["acknowledged"] = bool(r.get("acknowledged", 0))
        try:
            es.index(index=index, id=str(r["id"]), document=doc)
            ok += 1
        except Exception as e:
            print(f"  [!] Error ID {r['id']}: {e}")
            err += 1
    return ok, err


def sync_once(state: dict) -> dict:
    """Run one sync cycle. Returns updated state."""
    ts = datetime.now().strftime("%H:%M:%S")

    # Events
    new_events = get_new_events(state["last_event_id"])
    if new_events:
        ok, err = forward_batch(new_events, IDX_EVENTS)
        state["last_event_id"] = new_events[-1]["id"]
        print(f"[{ts}] Events: +{ok} indexed, {err} errors (last_id={state['last_event_id']})")
    else:
        print(f"[{ts}] Events: no new records")

    # Alerts
    new_alerts = get_new_alerts(state["last_alert_id"])
    if new_alerts:
        ok, err = forward_batch(new_alerts, IDX_ALERTS, is_alert=True)
        state["last_alert_id"] = new_alerts[-1]["id"]
        print(f"[{ts}] Alerts: +{ok} indexed, {err} errors (last_id={state['last_alert_id']})")
    else:
        print(f"[{ts}] Alerts: no new records")

    return state


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SentinelCore → ELK continuous sync")
    parser.add_argument("--interval", type=int, default=30,
                        help="Poll interval in seconds (default: 30)")
    parser.add_argument("--once", action="store_true",
                        help="Run a single sync and exit")
    parser.add_argument("--reset", action="store_true",
                        help="Reset sync state (re-export all records)")
    args = parser.parse_args()

    if not es.ping():
        print("[ERROR] Cannot connect to Elasticsearch at", ES_HOST)
        sys.exit(1)

    print(f"[SentinelCore → ELK Sync] Connected to {ES_HOST}")

    state = {"last_event_id": 0, "last_alert_id": 0} if args.reset else load_state()
    print(f"[Sync] Starting from event_id={state['last_event_id']}, alert_id={state['last_alert_id']}")

    if args.once:
        state = sync_once(state)
        save_state(state)
        return

    print(f"[Sync] Polling every {args.interval}s — Ctrl+C to stop\n")
    try:
        while True:
            state = sync_once(state)
            save_state(state)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[Sync] Stopped.")
        save_state(state)


if __name__ == "__main__":
    main()
