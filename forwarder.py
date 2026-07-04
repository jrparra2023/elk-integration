"""
SentinelCore → Elasticsearch Forwarder
Exporta eventos y alertas de SentinelCore a Elasticsearch
para visualización en Kibana.
"""

import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from elasticsearch import Elasticsearch

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH     = Path.home() / "sentinelcore/logs/sentinelcore.db"
ES_HOST     = "http://localhost:9200"
IDX_EVENTS  = "sentinelcore-events"
IDX_ALERTS  = "sentinelcore-alerts"

es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])

# ── Index templates ───────────────────────────────────────────────────────────

def create_indices():
    """Crea los índices con mappings correctos si no existen."""
    events_mapping = {
        "mappings": {
            "properties": {
                "timestamp":  {"type": "date"},
                "source":     {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "severity":   {"type": "keyword"},
                "src_ip":     {"type": "ip"},
                "dst_ip":     {"type": "ip"},
                "user":       {"type": "keyword"},
                "message":    {"type": "text"},
            }
        }
    }
    alerts_mapping = {
        "mappings": {
            "properties": {
                "created_at":  {"type": "date"},
                "rule_name":   {"type": "keyword"},
                "severity":    {"type": "keyword"},
                "description": {"type": "text"},
                "src_ip":      {"type": "ip"},
                "acknowledged":{"type": "boolean"},
            }
        }
    }
    for idx, mapping in [(IDX_EVENTS, events_mapping), (IDX_ALERTS, alerts_mapping)]:
        if not es.indices.exists(index=idx):
            es.indices.create(index=idx, body=mapping)
            print(f"[+] Índice creado: {idx}")
        else:
            print(f"[=] Índice ya existe: {idx}")

# ── DB helpers ────────────────────────────────────────────────────────────────

def get_events(since_id=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM events WHERE id > ? ORDER BY id ASC", (since_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_alerts(since_id=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM alerts WHERE id > ? ORDER BY id ASC", (since_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Forwarder ─────────────────────────────────────────────────────────────────

def forward_events(since_id=0):
    events = get_events(since_id)
    if not events:
        print("[~] No hay eventos nuevos para exportar.")
        return 0, 0

    ok = 0
    for e in events:
        # Limpia IPs vacías para evitar error de mapping
        doc = {k: v for k, v in e.items() if v is not None and v != ""}
        # Convierte timestamp a formato ISO si no lo tiene
        if "timestamp" in doc:
            doc["@timestamp"] = doc["timestamp"]
        try:
            es.index(index=IDX_EVENTS, id=str(e["id"]), document=doc)
            ok += 1
        except Exception as ex:
            print(f"[!] Error evento {e['id']}: {ex}")

    last_id = events[-1]["id"]
    print(f"[+] Eventos exportados: {ok}/{len(events)} (último ID: {last_id})")
    return ok, last_id

def forward_alerts(since_id=0):
    alerts = get_alerts(since_id)
    if not alerts:
        print("[~] No hay alertas nuevas para exportar.")
        return 0, 0

    ok = 0
    for a in alerts:
        doc = {k: v for k, v in a.items() if v is not None and v != ""}
        if "created_at" in doc:
            doc["@timestamp"] = doc["created_at"]
        doc["acknowledged"] = bool(a.get("acknowledged", 0))
        try:
            es.index(index=IDX_ALERTS, id=str(a["id"]), document=doc)
            ok += 1
        except Exception as ex:
            print(f"[!] Error alerta {a['id']}: {ex}")

    last_id = alerts[-1]["id"]
    print(f"[+] Alertas exportadas: {ok}/{len(alerts)} (último ID: {last_id})")
    return ok, last_id

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[SentinelCore → ELK] Conectando a {ES_HOST}...")
    if not es.ping():
        print("[ERROR] No se puede conectar a Elasticsearch.")
        sys.exit(1)
    print("[OK] Elasticsearch disponible.")

    create_indices()

    print("\n── Exportando eventos ──────────────────────")
    forward_events(since_id=0)

    print("\n── Exportando alertas ──────────────────────")
    forward_alerts(since_id=0)

    print("\n[SentinelCore → ELK] Exportación completa.")
