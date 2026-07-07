# Log Generator & Testing Simulator

An interactive, multi-pattern, structured logging simulator designed to help developers test and validate their logging infrastructure (e.g., Elasticsearch, Loki, Splunk, Datadog, Grafana, Prometheus).

## Features

- **Format Flexibility**: Toggle between structured **JSON logs (default)** and standard raw text logs at runtime.
- **Interactive Control Center**: Built-in, high-performance HTML/CSS dashboard with real-time stats and control dials.
- **Real-Time Stream**: Live stdout log feed inside the browser dashboard.
- **Custom Injections**: Trigger manual logs with specific severities and custom messages via UI or API.
- **Load Generators**: Simulate real-world traffic flows, including:
  - `random`: Random delay logging (default).
  - `constant`: Static timed interval logging.
  - `sinewave`: Sine-wave traffic simulation (matches diurnal loads).
  - `burst`: Auto-triggered severe fault log bursts.
- **Prometheus Metrics**: Native `/metrics` endpoint exposing telemetry about emitted log frequencies by level.

---

## Quick Start

### 1. Run Locally
```bash
python app.py
```
Then navigate to [http://localhost:8080](http://localhost:8080) in your browser.

### 2. Run with Docker
Build and run the container:
```bash
docker build -t log-generator .
docker run -p 8080:8080 log-generator
```

---

## Configuration Reference

Customize the generator's behavior using the following environment variables:

| Environment Variable | Default Value | Description |
| :--- | :--- | :--- |
| `LOG_FORMAT` | `JSON` | Format of emitted logs. Choice of `JSON` or `TEXT`. |
| `LOG_LEVEL` | `DEBUG` | Minimum log severity level allowed. |
| `LOG_PATTERN` | `random` | Logic pattern for log interval generation: `random`, `constant`, `sinewave`, `burst`. |
| `LOG_INTERVAL_MIN` | `10.0` | Minimum delay in seconds between generated logs. |
| `LOG_INTERVAL_MAX` | `15.0` | Maximum delay in seconds between generated logs. |
| `LOG_FIELDS` | *(None)* | Comma-separated key-value pairs of metadata added to JSON logs (e.g., `env=production,service=auth`). |
| `PORT` or `HTTP_PORT` | `8080` | Network port for dashboard, API, and Prometheus endpoint. |

---

## API Documentation

### GET `/`
Serves the dynamic glassmorphic diagnostic dashboard.

### GET `/metrics`
Exposes Prometheus telemetry. Example output:
```text
# HELP log_generator_emitted_logs_total Total number of logs generated.
# TYPE log_generator_emitted_logs_total counter
log_generator_emitted_logs_total{level="DEBUG"} 12
log_generator_emitted_logs_total{level="INFO"} 45
log_generator_uptime_seconds 123.45
```

### POST `/api/log`
Manually inject a custom log message.
```bash
curl -X POST http://localhost:8080/api/log \
  -H "Content-Type: application/json" \
  -d '{"level": "WARNING", "message": "Simulated hardware alert"}'
```

### POST `/api/burst`
Inject a sudden flurry of severe logs to test system alert limits.
```bash
curl -X POST http://localhost:8080/api/burst \
  -H "Content-Type: application/json" \
  -d '{"count": 50}'
```

### POST `/api/config`
Dynamically alter simulator settings without restarting.
```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{"format_type": "TEXT", "pattern": "sinewave", "interval_min": 1.0, "interval_max": 3.0}'
```
