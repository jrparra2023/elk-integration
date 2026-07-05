#!/usr/bin/env python3
"""
SentinelCore → ELK — export_dashboard.py
Exports the SentinelCore Kibana dashboard as an .ndjson file
for one-click import into any Kibana instance.

Usage
-----
python3 export_dashboard.py                         # exports all dashboards
python3 export_dashboard.py --list                  # list available dashboards
python3 export_dashboard.py --id <dashboard_id>     # export specific dashboard
"""

import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime

KIBANA_HOST  = "http://localhost:5601"
EXPORT_DIR   = Path(__file__).parent / "kibana_exports"


def list_dashboards() -> list[dict]:
    """List all dashboards in Kibana."""
    r = requests.get(
        f"{KIBANA_HOST}/api/saved_objects/_find",
        params={"type": "dashboard", "per_page": 50},
        headers={"kbn-xsrf": "true"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json().get("saved_objects", [])


def export_dashboard(dashboard_id: str, output_path: Path):
    """Export a dashboard and all its dependencies as NDJSON."""
    r = requests.post(
        f"{KIBANA_HOST}/api/saved_objects/_export",
        headers={"kbn-xsrf": "true", "Content-Type": "application/json"},
        json={
            "objects": [{"type": "dashboard", "id": dashboard_id}],
            "includeReferencesDeep": True,
        },
        timeout=30,
    )
    r.raise_for_status()
    output_path.write_bytes(r.content)
    lines = len(r.content.splitlines())
    print(f"[+] Exported {lines} objects → {output_path}")


def export_all_dashboards():
    """Export all dashboards found in Kibana."""
    dashboards = list_dashboards()
    if not dashboards:
        print("[~] No dashboards found in Kibana.")
        return

    EXPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    for d in dashboards:
        name    = d["attributes"].get("title", "untitled").replace(" ", "_").replace("/", "-")
        did     = d["id"]
        outfile = EXPORT_DIR / f"{name}_{ts}.ndjson"
        print(f"[~] Exporting: {d['attributes'].get('title')} ({did})")
        try:
            export_dashboard(did, outfile)
        except Exception as e:
            print(f"[!] Failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Export Kibana dashboards as NDJSON")
    parser.add_argument("--list", action="store_true", help="List available dashboards")
    parser.add_argument("--id",   metavar="DASHBOARD_ID", help="Export specific dashboard by ID")
    args = parser.parse_args()

    # Test Kibana connection
    try:
        r = requests.get(f"{KIBANA_HOST}/api/status", timeout=5)
        status = r.json().get("status", {}).get("overall", {}).get("level", "unknown")
        print(f"[OK] Kibana status: {status}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Kibana: {e}")
        sys.exit(1)

    if args.list:
        dashboards = list_dashboards()
        if not dashboards:
            print("No dashboards found.")
        for d in dashboards:
            print(f"  {d['id']}  →  {d['attributes'].get('title', 'untitled')}")
        return

    if args.id:
        EXPORT_DIR.mkdir(exist_ok=True)
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile = EXPORT_DIR / f"dashboard_{args.id}_{ts}.ndjson"
        export_dashboard(args.id, outfile)
        return

    # Default: export all
    export_all_dashboards()
    print(f"\n[Done] Exports saved to {EXPORT_DIR}/")
    print("[Import] In any Kibana: Stack Management → Saved Objects → Import → select .ndjson")


if __name__ == "__main__":
    main()
