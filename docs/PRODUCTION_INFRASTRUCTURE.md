# Production Infrastructure Manual

This document details the production-ready deployment infrastructure for the **Enterprise Platform**.

---

## 🏗️ Topology Architecture

```mermaid
graph TD
    User[Clients / Web Control Center] --> Nginx[Nginx Reverse Proxy + SSL/TLS]
    
    subgraph K8s / Docker Stack [Kubernetes / Docker Compose]
        Nginx --> FastAPI[FastAPI Core Backend (3 Replicas)]
        FastAPI --> Postgres[(PostgreSQL 16 Multi-AZ)]
        FastAPI --> Redis[(Redis 7 Cache & Locks)]
        FastAPI --> Qdrant[(Qdrant Vector DB)]
        FastAPI --> Redpanda[(Redpanda / Kafka Event Broker)]
    end

    subgraph Monitoring & Logging Stack
        Prometheus[Prometheus Server] --> FastAPI
        Prometheus --> Postgres
        Prometheus --> Redis
        Grafana[Grafana Dashboards] --> Prometheus
        Loki[Grafana Loki Logs] --> Promtail[Promtail Container Collector]
    end

    subgraph Disaster Recovery
        BackupScript[backup_recovery.sh] --> S3[(AWS S3 Encrypted Backup Bucket)]
    end
```

---

## 📦 Deployment Manifests & Configuration

1. **Docker Container Stack**
   - [`backend/Dockerfile`](file:///home/aryan/Videos/IRE/backend/Dockerfile): Multi-stage Python 3.12 production container.
   - [`docker-compose.yml`](file:///home/aryan/Videos/IRE/docker-compose.yml): Local development environment.
   - [`docker-compose.prod.yml`](file:///home/aryan/Videos/IRE/docker-compose.prod.yml): Hardened production compose setup with Nginx SSL proxy, PostgreSQL, Redis, Qdrant, Redpanda, FastAPI backend, Prometheus, Grafana, and Loki.

2. **GitHub Actions CI/CD Pipeline** ([`.github/workflows/ci-cd.yml`](file:///home/aryan/Videos/IRE/.github/workflows/ci-cd.yml))
   - Automated testing on `push` and `pull_request`: Runs all 38 pytest unit & integration tests (`test_ai_infrastructure.py`, `test_rule_engine_framework.py`, `test_enterprise_agent_framework.py`, `test_enterprise_integration_platform.py`).
   - Builds multi-arch Docker images, validates Terraform IaC specs, and performs Kubernetes dry-run deployment rollouts.

3. **Terraform Infrastructure as Code** ([`infrastructure/terraform/`](file:///home/aryan/Videos/IRE/infrastructure/terraform/))
   - `main.tf`: AWS VPC, public & private subnets, S3 encrypted storage, Multi-AZ RDS PostgreSQL cluster, and ElastiCache Redis.
   - `variables.tf` & `outputs.tf`: Parameterized region, CIDRs, and connection strings.

4. **Kubernetes (K8s) Cluster Manifests** ([`infrastructure/k8s/`](file:///home/aryan/Videos/IRE/infrastructure/k8s/))
   - `namespace.yaml`: Production namespace `ire-production`.
   - `configmap-secrets.yaml`: ConfigMap & Secret definitions.
   - `backend-deployment.yaml`: Deployment with 3 replicas, resource CPU/Memory requests & limits, liveness & readiness probes, ClusterIP Service, and HorizontalPodAutoscaler (`min: 3`, `max: 20`).
   - `ingress.yaml`: Nginx Ingress Controller with SSL termination (`api.ire.health`) and rate limiting (`100 r/s`).

5. **Nginx Reverse Proxy & SSL** ([`infrastructure/nginx/`](file:///home/aryan/Videos/IRE/infrastructure/nginx/))
   - `nginx.conf`: Nginx reverse proxy with TLS 1.2/1.3, HTTP/2, rate-limiting zones (`100r/s`), security headers (HSTS, X-Frame-Options, X-Content-Type-Options), and upstream load balancing.
   - `generate_ssl_certs.sh`: Shell script generating 2048-bit RSA TLS certificates in `infrastructure/nginx/certs/`.

6. **Monitoring & Alerting (Prometheus & Grafana)** ([`infrastructure/monitoring/`](file:///home/aryan/Videos/IRE/infrastructure/monitoring/))
   - `prometheus.yml`: Scrape target configurations for FastAPI backend `/metrics`, microservices, Redis, and PostgreSQL.
   - `platform_dashboard.json`: Provisioned Grafana dashboard tracking API Request Rate, P99 Latency, AI Gateway Fallback Rate, and Rule Engine execution frequencies.

7. **Centralized Logging** ([`docker-compose.prod.yml`](file:///home/aryan/Videos/IRE/docker-compose.prod.yml))
   - Grafana Loki (`port 3100`) collecting container log stdout/stderr streams.

8. **Backup & Recovery Automation** ([`infrastructure/scripts/backup_recovery.sh`](file:///home/aryan/Videos/IRE/infrastructure/scripts/backup_recovery.sh))
   - `backup`: Dumps PostgreSQL database (`pg_dump`), compresses with gzip, encrypts with AES-256 (`openssl enc -pbkdf2`), and uploads to AWS S3 (`s3://ire-enterprise-backups`).
   - `restore <file>`: Decrypts AES-256 backup, decompresses, and restores database schema & data via `psql`.

---

## 🚀 Execution & Deployment Quickstart

### 1. Local Production Stack via Docker Compose

```bash
# 1. Generate SSL Certificates
bash infrastructure/nginx/generate_ssl_certs.sh

# 2. Launch Production Stack
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Backup & Disaster Recovery Execution

```bash
# Execute AES-256 Encrypted Backup
bash infrastructure/scripts/backup_recovery.sh backup

# Restore Database from Encrypted Backup
bash infrastructure/scripts/backup_recovery.sh restore /tmp/ire_backups/backup_ire_production_db_20260801_110000.sql.gz.enc
```
