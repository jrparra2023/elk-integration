#!/usr/bin/env python3
"""
SentinelCore → ELK — create_alerts.py
Crea Kibana alerting rules mapeadas a las reglas de SentinelCore.
"""

import sys
import json
import argparse
import requests

KIBANA_HOST = "http://localhost:5601"
HEADERS     = {"kbn-xsrf": "true", "Content-Type": "application/json"}
RULE_TAG    = "sentinelcore"

RULES = [
    {
        "name": "[SentinelCore] SSH Brute Force",
        "tags": [RULE_TAG, "ssh", "brute_force"],
        "rule_type_id": ".es-query",
        "consumer": "alerts",
        "schedule": {"interval": "1m"},
        "notify_when": "onActiveAlert",
        "actions": [],
        "params": {
            "size": 100,
            "index": ["sentinelcore-events"],
            "timeField": "@timestamp",
            "timeWindowSize": 1,
            "timeWindowUnit": "m",
            "thresholdComparator": ">=",
            "threshold": [5],
            "searchType": "esQuery",
            "esQuery": json.dumps({
                "query": {
                    "bool": {
                        "filter": [
                            {"term": {"event_type": "auth_failure"}}
                        ]
                    }
                }
            }),
            "excludeHitsFromPreviousRun": True,
        },
    },
    {
        "name": "[SentinelCore] Port Scan Detected",
        "tags": [RULE_TAG, "port_scan"],
        "rule_type_id": ".es-query",
        "consumer": "alerts",
        "schedule": {"interval": "1m"},
        "notify_when": "onActiveAlert",
        "actions": [],
        "params": {
            "size": 100,
            "index": ["sentinelcore-events"],
            "timeField": "@timestamp",
            "timeWindowSize": 5,
            "timeWindowUnit": "m",
            "thresholdComparator": ">=",
            "threshold": [1],
            "searchType": "esQuery",
            "esQuery": json.dumps({
                "query": {
                    "term": {"event_type": "port_scan"}
                }
            }),
            "excludeHitsFromPreviousRun": True,
        },
    },
    {
        "name": "[SentinelCore] Unknown Device Alert",
        "tags": [RULE_TAG, "intrusion", "homeguard"],
        "rule_type_id": ".es-query",
        "consumer": "alerts",
        "schedule": {"interval": "5m"},
        "notify_when": "onActiveAlert",
        "actions": [],
        "params": {
            "size": 100,
            "index": ["sentinelcore-events"],
            "timeField": "@timestamp",
            "timeWindowSize": 60,
            "timeWindowUnit": "m",
            "thresholdComparator": ">=",
            "threshold": [1],
            "searchType": "esQuery",
            "esQuery": json.dumps({
                "query": {
                    "term": {"event_type": "unknown_device"}
                }
            }),
            "excludeHitsFromPreviousRun": True,
        },
    },
    {
        "name": "[SentinelCore] Web Scanner",
        "tags": [RULE_TAG, "web_scan"],
        "rule_type_id": ".es-query",
        "consumer": "alerts",
        "schedule": {"interval": "2m"},
        "notify_when": "onActiveAlert",
        "actions": [],
        "params": {
            "size": 100,
            "index": ["sentinelcore-events"],
            "timeField": "@timestamp",
            "timeWindowSize": 2,
            "timeWindowUnit": "m",
            "thresholdComparator": ">=",
            "threshold": [20],
            "searchType": "esQuery",
            "esQuery": json.dumps({
                "query": {
                    "term": {"event_type": "web_scan"}
                }
            }),
            "excludeHitsFromPreviousRun": True,
        },
    },
]

def kibana_ok():
    try:
        r = requests.get(f"{KIBANA_HOST}/api/status", timeout=5)
        return r.json().get("status", {}).get("overall", {}).get("level") == "available"
    except:
        return False

def create_rule(rule):
    r = requests.post(
        f"{KIBANA_HOST}/api/alerting/rule",
        headers=HEADERS,
        json=rule,
        timeout=15,
    )
    return r.json()

def list_rules():
    r = requests.get(
        f"{KIBANA_HOST}/api/alerting/rules/_find",
        params={"per_page": 50},
        headers=HEADERS,
        timeout=10,
    )
    rules = r.json().get("data", [])
    return [x for x in rules if RULE_TAG in x.get("tags", [])]

def delete_rule(rule_id):
    requests.delete(f"{KIBANA_HOST}/api/alerting/rule/{rule_id}", headers=HEADERS, timeout=10)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list",   action="store_true")
    parser.add_argument("--delete", action="store_true")
    args = parser.parse_args()

    if not kibana_ok():
        print(f"[ERROR] Kibana no disponible en {KIBANA_HOST}")
        sys.exit(1)
    print("[OK] Kibana disponible")

    if args.list:
        rules = list_rules()
        print(f"\n{len(rules)} regla(s) SentinelCore:")
        for r in rules:
            print(f"  [{r['id']}] {r['name']}")
        return

    if args.delete:
        rules = list_rules()
        for r in rules:
            delete_rule(r["id"])
            print(f"[-] Eliminada: {r['name']}")
        return

    print(f"\nCreando {len(RULES)} reglas de alerta en Kibana...\n")
    ok = 0
    for rule in RULES:
        result = create_rule(rule)
        if "id" in result:
            print(f"[+] Creada: {rule['name']} (id: {result['id']})")
            ok += 1
        else:
            msg = result.get("message", str(result))[:120]
            print(f"[!] Falló: {rule['name']}")
            print(f"    {msg}")

    print(f"\n[Done] {ok}/{len(RULES)} reglas creadas.")
    print(f"[Ver] Kibana → Stack Management → Rules")

if __name__ == "__main__":
    main()
