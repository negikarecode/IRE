# Enterprise Logging & Observability Guide

This document details the enterprise logging architecture, Request ID tracing, HIPAA-compliant PHI redaction, latency tracking, and ELK / Grafana Loki integration guidelines for the Insurance Reasoning Engine (IRE) platform.

---

## 1. Logging Architecture & Capabilities

The platform implements a structured JSON logging system designed for high-throughput log ingestion pipelines (Logstash/Filebeat, Grafana Alloy/Promtail, Datadog Agent).

### Core Features
- **Structured JSON Output**: Every log entry is formatted as a single-line JSON object.
- **Request ID Tracing**: Incoming requests are tagged with a unique `X-Request-ID` (UUIDv4) that propagates through all async calls and backend services.
- **HIPAA-Compliant PHI & Credential Redaction**: Automatically scans and redacts sensitive keys (`password`, `token`, `refresh_token`, `secret`, `ssn`, `patient_name`, `dob`, `address`, `phone`).
- **Processing Time Tracking**: Records exact execution latency in milliseconds (`processing_time_ms`) for every API endpoint.
- **Subsystem Loggers**: Categorized loggers (`ire.api`, `ire.auth`, `ire.uploads`, `ire.ocr`, `ire.jobs`, `ire.db`, `ire.errors`).

---

## 2. Standardized JSON Log Schema

```json
{
    "timestamp": "2026-08-01T20:15:00.123456+00:00",
    "level": "INFO",
    "logger": "ire.api",
    "message": "HTTP POST /api/v1/auth/hospitals/login -> 200 (42.15 ms)",
    "service": "ire-backend",
    "environment": "production",
    "request_id": "req_2e05f445c9d9490daa68b36b6d18f639",
    "tenant_id": "tenant_default",
    "hospital_id": "hosp_9021",
    "user_id": "usr_4012",
    "extra": {
        "event": "http_request",
        "method": "POST",
        "path": "/api/v1/auth/hospitals/login",
        "query_params": {},
        "status_code": 200,
        "processing_time_ms": 42.15,
        "client_ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0..."
    }
}
```

---

## 3. Grafana Loki & ELK Integration

### Grafana Loki (Promtail / Grafana Alloy) Configuration
Promtail pipeline stage to parse the JSON logs and index labels:

```yaml
scrape_configs:
  - job_name: ire-backend-logs
    static_configs:
      - targets: ['localhost']
        labels:
          job: ire-backend
          __path__: /var/log/ire/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            logger: logger
            request_id: request_id
            tenant_id: tenant_id
            hospital_id: hospital_id
            processing_time_ms: extra.processing_time_ms
      - labels:
          level:
          logger:
          request_id:
          tenant_id:
          hospital_id:
```

### Logstash (ELK Stack) Pipeline Configuration
Logstash filter stage:

```ruby
filter {
  json {
    source => "message"
  }
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }
}
```

---

## 4. Verification

Run the test suite to verify log formatter execution and middleware integration:

```bash
cd backend
PYTHONPATH=. pytest
```
