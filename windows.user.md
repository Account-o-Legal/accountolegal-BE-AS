# Windows Native Observability Setup (No Docker)

This guide helps Windows teams run the full observability stack as native Windows processes without Docker or WSL.

Stack includes:

- Prometheus
- Grafana
- Tempo
- Loki
- OpenTelemetry Collector

---

# Why This Setup

Many Windows teams run into:

- Docker Desktop memory overhead
- WSL networking issues
- File permission headaches
- Slow bind mounts
- Corporate restrictions around virtualization

This setup avoids all of that.

Everything runs as lightweight native Windows binaries.

---

# Folder Structure

After setup, your folder should look like this:

```txt
C:\observability
│
├── grafana
├── prometheus
├── tempo-data
├── loki-data
├── otelcol-config
│
├── tempo_2.6.0_windows_amd64.exe
├── loki-windows-amd64.exe
├── otelcol-contrib.exe
│
└── start.ps1
````

---

# Step 1 — Download All Binaries

Open PowerShell:

```powershell
mkdir C:\observability
cd C:\observability

# Prometheus
Invoke-WebRequest -Uri "https://github.com/prometheus/prometheus/releases/download/v2.54.1/prometheus-2.54.1.windows-amd64.zip" -OutFile prometheus.zip
Expand-Archive prometheus.zip -DestinationPath .
Rename-Item prometheus-2.54.1.windows-amd64 prometheus

# Grafana
Invoke-WebRequest -Uri "https://dl.grafana.com/oss/release/grafana-11.2.0.windows-amd64.zip" -OutFile grafana.zip
Expand-Archive grafana.zip -DestinationPath .
Rename-Item grafana-v11.2.0 grafana

# Tempo
Invoke-WebRequest -Uri "https://github.com/grafana/tempo/releases/download/v2.6.0/tempo_2.6.0_windows_amd64.zip" -OutFile tempo.zip
Expand-Archive tempo.zip -DestinationPath .
mkdir tempo-data

# Loki
Invoke-WebRequest -Uri "https://github.com/grafana/loki/releases/download/v3.2.0/loki-windows-amd64.exe.zip" -OutFile loki.zip
Expand-Archive loki.zip -DestinationPath .
mkdir loki-data

# OpenTelemetry Collector
Invoke-WebRequest -Uri "https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.108.0/otelcol-contrib_0.108.0_windows_amd64.tar.gz" -OutFile otelcol.tar.gz
tar -xf otelcol.tar.gz
mkdir otelcol-config
```

---

# Step 2 — Configure OpenTelemetry Collector

Create:

```txt
C:\observability\otelcol-config\config.yaml
```

Add:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s

  memory_limiter:
    check_interval: 5s
    limit_mib: 256

exporters:
  prometheusremotewrite:
    endpoint: http://localhost:9090/api/v1/write
    tls:
      insecure: true

  otlp/tempo:
    endpoint: http://localhost:4327
    tls:
      insecure: true

  loki:
    endpoint: http://localhost:3100/loki/api/v1/push
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

---

# Step 3 — Configure Prometheus

Replace:

```txt
C:\observability\prometheus\prometheus.yml
```

with:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: accounting-app
    static_configs:
      - targets: ["localhost:8000"]
    metrics_path: /metrics

  - job_name: otel-collector
    static_configs:
      - targets: ["localhost:8888"]
```

---

# Step 4 — Configure Tempo

Create:

```txt
C:\observability\tempo-data\tempo.yaml
```

Add:

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4327

ingester:
  max_block_duration: 5m

storage:
  trace:
    backend: local

    local:
      path: C:\observability\tempo-data\blocks

    wal:
      path: C:\observability\tempo-data\wal

compactor:
  compaction:
    block_retention: 48h
```

---

# Step 5 — Configure Loki

Create:

```txt
C:\observability\loki-data\loki.yaml
```

Add:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: C:\observability\loki-data

  storage:
    filesystem:
      chunks_directory: C:\observability\loki-data\chunks
      rules_directory: C:\observability\loki-data\rules

  replication_factor: 1

  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13

      index:
        prefix: index_
        period: 24h
```

---

# Step 6 — Start Services

Open 4 separate PowerShell terminals.

## Terminal 1 — Prometheus

```powershell
C:\observability\prometheus\prometheus.exe --config.file=C:\observability\prometheus\prometheus.yml --web.enable-remote-write-receiver
```

---

## Terminal 2 — Tempo

```powershell
C:\observability\tempo_2.6.0_windows_amd64.exe -config.file=C:\observability\tempo-data\tempo.yaml
```

---

## Terminal 3 — Loki

```powershell
C:\observability\loki-windows-amd64.exe -config.file=C:\observability\loki-data\loki.yaml
```

---

## Terminal 4 — OpenTelemetry Collector

```powershell
C:\observability\otelcol-contrib.exe --config=C:\observability\otelcol-config\config.yaml
```

---

# Step 7 — Start Grafana

Run:

```powershell
C:\observability\grafana\bin\grafana-server.exe --homepath C:\observability\grafana
```

Open:

```txt
http://localhost:3000
```

Default login:

```txt
Username: admin
Password: admin
```

---

# Step 8 — Add Grafana Datasources

Go to:

```txt
Connections → Data Sources
```

Add these datasources:

| Name       | Type       | URL                                            |
| ---------- | ---------- | ---------------------------------------------- |
| Prometheus | Prometheus | [http://localhost:9090](http://localhost:9090) |
| Tempo      | Tempo      | [http://localhost:3200](http://localhost:3200) |
| Loki       | Loki       | [http://localhost:3100](http://localhost:3100) |

---

# Step 9 — Enable Trace ↔ Logs Correlation

Inside the Tempo datasource settings:

* Scroll to Trace to Logs
* Select Loki datasource
* Save

This enables:

* Trace → Logs navigation
* Logs → Trace linking
* Full distributed debugging flow

---

# Step 10 — Configure Your FastAPI App

Add to `.env`:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=accounting-software
APP_ENV=development
```

Start the app:

```bash
uvicorn app.main:app --reload --port 8000
```

---

# One-Click Startup Script

Create:

```txt
C:\observability\start.ps1
```

Add:

```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\observability\prometheus\prometheus.exe --config.file=C:\observability\prometheus\prometheus.yml --web.enable-remote-write-receiver"

Start-Sleep 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\observability\tempo_2.6.0_windows_amd64.exe -config.file=C:\observability\tempo-data\tempo.yaml"

Start-Sleep 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\observability\loki-windows-amd64.exe -config.file=C:\observability\loki-data\loki.yaml"

Start-Sleep 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\observability\otelcol-contrib.exe --config=C:\observability\otelcol-config\config.yaml"

Start-Sleep 2

Start-Process powershell -ArgumentList "-NoExit", "-Command", "C:\observability\grafana\bin\grafana-server.exe --homepath C:\observability\grafana"

Write-Host "All observability services started."
Write-Host "Grafana available at http://localhost:3000"
```

Run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then:

```powershell
.\start.ps1
```

---

# Ports Reference

| Service               | URL                                            |
| --------------------- | ---------------------------------------------- |
| Grafana               | [http://localhost:3000](http://localhost:3000) |
| Prometheus            | [http://localhost:9090](http://localhost:9090) |
| Tempo                 | [http://localhost:3200](http://localhost:3200) |
| Loki                  | [http://localhost:3100](http://localhost:3100) |
| OTel Collector (gRPC) | localhost:4317                                 |
| OTel Collector (HTTP) | localhost:4318                                 |

---

# Recommended Next Steps

After this is working:

* Add OpenTelemetry instrumentation to FastAPI
* Export structured logs
* Add request tracing
* Create Grafana dashboards
* Add alerts for errors and latency
* Enable production-grade retention policies

---

# Common Windows Issues

## Port Already in Use

Check:

```powershell
netstat -ano | findstr :3000
```

Kill process:

```powershell
taskkill /PID <PID> /F
```

---

## PowerShell Execution Policy Error

Run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

---

## Firewall Prompt

Allow access for:

* Grafana
* Prometheus
* Loki
* Tempo
* OTel Collector

on private networks.

---

# Final Result

You now have a fully local observability stack running natively on Windows with:

* Metrics
* Logs
* Distributed tracing
* Correlation across all telemetry
* Zero Docker dependency

```
```
