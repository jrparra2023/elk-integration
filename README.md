# ELK Integration — SentinelCore → Elasticsearch + Kibana

Python forwarder that exports SentinelCore events and alerts into Elasticsearch for visualization in Kibana.

Fourth project in a cybersecurity portfolio: **NetWatch → HomeGuard → SentinelCore → ELK Integration**

## Stack
| Tool | Purpose |
|---|---|
| Elasticsearch 8.x | Event storage and search |
| Kibana 8.x | Security dashboards |
| Python 3 | Forwarder script |
| elasticsearch-py 8.x | Python client |

## Architecture
## Setup
```bash
# Install Elasticsearch + Kibana
sudo apt-get install elasticsearch kibana

# Install Python client
pip install "elasticsearch>=8.0.0,<9.0.0"

# Run forwarder
python3 forwarder.py
```

## Kibana Dashboards
- **Eventos por Fuente** — pie chart of log sources
- **Eventos por Tipo** — bar chart of event types over time
- **Top IPs** — table of most active source IPs
- **Alertas por Severidad** — alert severity breakdown

## Author
José Rafael Parra Dugarte
Electronics & Telecommunications Engineering — Universidad del Cauca
[github.com/jrparra2023](https://github.com/jrparra2023)
