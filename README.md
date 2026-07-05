# 📊 ELK Integration — SentinelCore → Elasticsearch + Kibana

Python forwarder that exports SentinelCore security events and alerts into Elasticsearch for real-time visualization in Kibana dashboards.

Fourth project in a cybersecurity portfolio: **NetWatch → HomeGuard → SentinelCore → ELK Integration**

---

## Features

- **Python forwarder** — exports SentinelCore SQLite events and alerts into Elasticsearch with correct field mappings
- **Automatic index creation** — creates `sentinelcore-events` and `sentinelcore-alerts` indices with typed mappings on first run
- **Incremental export** — supports `since_id` parameter to export only new records
- **4 Kibana dashboards** — pre-built security visualizations over real SentinelCore data
- **208 events indexed** — auth failures, web scans, port scans, DNS anomalies, syslog events across 6 sources

---

## Stack

| Tool | Purpose |
|---|---|
| Elasticsearch 8.19 | Event storage, search, and indexing |
| Kibana 8.19 | Security dashboard visualization |
| Python 3.13 | Forwarder script |
| elasticsearch-py 8.x | Official Python client |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SentinelCore (SQLite)                   │
│                                                             │
│   events table  ──────────────────────────────────────┐    │
│   alerts table  ──────────────────────────────────┐   │    │
└───────────────────────────────────────────────────│───│────┘
                                                    │   │
                                                    ▼   ▼
                                ┌───────────────────────────┐
                                │       forwarder.py        │
                                │    (sync.py continuous)   │
                                └──────────┬────────────────┘
                                           │
                          ┌────────────────▼────────────────┐
                          │         Elasticsearch 8.x       │
                          │  sentinelcore-events (208 docs) │
                          │  sentinelcore-alerts  (9 docs)  │
                          └────────────────┬────────────────┘
                                           │
                          ┌────────────────▼────────────────┐
                          │            Kibana 8.x           │
                          │  • Eventos por Fuente (pie)     │
                          │  • Eventos por Tipo (bar)       │
                          │  • Top IPs (table)              │
                          │  • Alertas por Severidad (pie)  │
                          │  • 4 Alerting rules             │
                          └─────────────────────────────────┘
```

---

## Setup

### 1. Install Elasticsearch + Kibana (Kali Linux)
```bash
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elastic-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/elastic-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update && sudo apt-get install -y elasticsearch kibana
```

### 2. Configure Elasticsearch (no SSL for local lab)
```bash
sudo tee /etc/elasticsearch/elasticsearch.yml > /dev/null << 'CONF'
cluster.name: sentinelcore-lab
node.name: kali-node-1
network.host: 127.0.0.1
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false
CONF
sudo systemctl enable --now elasticsearch kibana
```

### 3. Install Python client
```bash
pip install "elasticsearch>=8.0.0,<9.0.0"
```

### 4. Run forwarder
```bash
# Make sure SentinelCore has ingested data first:
cd ~/sentinelcore && source venv/bin/activate
python3 ingest.py --all-samples

# Then export to Elasticsearch:
cd ~/elk-integration
python3 forwarder.py
```

---

## Usage

```bash
# Start ELK stack
sudo systemctl start elasticsearch kibana

# Verify Elasticsearch
curl -s http://localhost:9200 | python3 -m json.tool | grep cluster_name

# Run forwarder
python3 forwarder.py

# Open Kibana
# http://localhost:5601
```

---

## Kibana Dashboards

**SentinelCore — Security Dashboard** contains 4 visualizations:

| Panel | Type | Description |
|---|---|---|
| Eventos por Fuente | Pie chart | Distribution of events by log source (auth_log, nginx, suricata, syslog, netwatch, homeguard) |
| Eventos por Tipo | Stacked bar | Event types over time (web_scan, auth_failure, port_scan, dns_anomaly, etc.) |
| Top IPs | Table | Most active source IPs by event count — identifies top attackers |
| Alertas por Severidad | Pie chart | Alert breakdown by severity (CRITICAL / HIGH / MEDIUM / LOW) |

### Sample data indexed
sentinelcore-events: 208 documents

auth_log   : 26.9%  (SSH failures, sudo commands, user creation)
nginx      : 44.2%  (web scans, 404 floods, 401 errors)
syslog     : 15.4%  (service failures, OOM, disk errors)
suricata   :  5.8%  (IDS alerts — port scans, SQL injection)
netwatch   :  3.9%  (port scan detections)
homeguard  :  3.8%  (unknown device alerts)

sentinelcore-alerts: 9 documents

suricata_port_scan  : HIGH
suricata_web_attack : HIGH
nginx_web_scanner   : HIGH (192.168.1.99 — 120 events, MALICIOUS reputation)
---

## Data View Setup (Kibana)

1. Open `http://localhost:5601`
2. ☰ → Stack Management → Data Views → Create data view
3. Name: `sentinelcore-events` | Index pattern: `sentinelcore-events` | Timestamp: `@timestamp`
4. Repeat for `sentinelcore-alerts`
5. ☰ → Analytics → Dashboards → Create dashboard → Add visualizations

---

## Integration with SentinelCore

This project is the observability layer for [SentinelCore](https://github.com/jrparra2023/sentinelcore):

- SentinelCore ingests 6 log sources, correlates events using 12 YAML rules, and stores results in SQLite
- This forwarder bridges the gap between SentinelCore's local SQLite store and the Elasticsearch/Kibana stack
- Together they form a complete SOC pipeline: **ingest → normalize → correlate → visualize**

---

## Roadmap

- [x] Python forwarder (events + alerts)
- [x] Automatic index creation with field mappings
- [x] 4 Kibana security dashboards
- [x] Kibana dashboard export (`.ndjson`) for one-click import
- [x] Continuous sync mode (poll every N seconds)
- [x] Kibana alerting rules mapped to SentinelCore correlation rules
- [x] Docker Compose with Elasticsearch + Kibana + forwarder

---

## Author

**José Rafael Parra Dugarte**
Electronics & Telecommunications Engineering Student  — Universidad del Cauca
Researcher @ GRIAL Wireless Networks Research Group
[LinkedIn](https://www.linkedin.com/in/josé-rafael-parra-dugarte) · [GitHub](https://github.com/jrparra2023)
