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