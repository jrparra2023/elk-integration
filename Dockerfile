FROM python:3.13-slim

LABEL maintainer="José Rafael Parra Dugarte <joserafaelparrad@gmail.com>"
LABEL description="SentinelCore → ELK Forwarder"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY forwarder.py sync.py export_dashboard.py create_alerts.py ./

RUN mkdir -p /app/state /app/kibana_exports

CMD ["python3", "sync.py", "--interval", "30"]
