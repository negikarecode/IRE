# Enterprise Production Deployment & Pipeline Guide

**Version**: 1.0.0  
**CI/CD Pipeline**: GitHub Actions (`.github/workflows/deploy.yml`)  
**Containerization**: Docker & Docker Compose (`docker-compose.prod.yml`)  
**Database Migration**: Alembic (`alembic upgrade head`)  
**Rollback Automation**: Emergency Recovery Script (`scripts/deploy_rollback.sh`)

---

## 1. Automated Deployment Pipeline Architecture

```
[Git Push to 'main'] ──> [1. Lint & Syntax Check]
                                   │
                                   v
                        [2. Automated Pytest Suite]
                        (100% Pass Rate Required)
                                   │
                                   v
                        [3. Multi-Stage Docker Build]
                        (FastAPI Backend & React Frontend)
                                   │
                                   v
                        [4. Database Schema Migration]
                        (Alembic upgrade head)
                                   │
                                   v
                        [5. Zero-Downtime Deployment]
                        (Container traffic shift)
                                   │
                                   v
                        [6. Health Check Verification]
                         /api/v1/health (HTTP 200)
                                   │
                   ┌───────────────┴───────────────┐
                   │                               │
                [PASSED]                       [FAILED]
           Deployment Success           Automated Rollback Triggered
                                        (scripts/deploy_rollback.sh)
```

---

## 2. GitHub Actions Workflow Configuration

The deployment pipeline is fully automated in [`.github/workflows/deploy.yml`](file:///home/aryan/Videos/IRE/.github/workflows/deploy.yml):

### Stages Included:
1. **Linting & Syntax Verification**: Executes `flake8` static code analysis.
2. **Automated Testing**: Runs pytest test suite across 59 unit/integration test suites.
3. **Multi-Stage Docker Packaging**: Builds optimized Python 3.12 slim images with non-root security.
4. **Database Migrations**: Runs `alembic upgrade head` before traffic routing.
5. **Deployment Verification & Rollback**: Verifies `/api/v1/health` endpoint within 60 seconds; automatically executes `scripts/deploy_rollback.sh` on failure.

---

## 3. Environment Variables & Secrets Management

Production configuration is driven by environment variables injected safely from **GitHub Repository Secrets**:

### Secret Keys Table
| Key Name | Description | Example / Required Format |
| :--- | :--- | :--- |
| `SECRET_KEY` | JWT signing secret key | 64-char hex (`openssl rand -hex 32`) |
| `POSTGRES_PASSWORD` | PostgreSQL admin user password | High-entropy string |
| `DATABASE_URL` | Async SQLAlchemy database URI | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `REDIS_HOST` | Redis cache hostname | `redis` or AWS ElastiCache endpoint |
| `OPENAI_API_KEY` | OpenAI API key for LLM fallbacks | `sk-proj-...` |

---

## 4. Manual & Emergency Operations

### Manual Deployment Command
To trigger a production deployment locally or from a deployment server:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Database Schema Migration
Run Alembic database migrations manually:

```bash
cd backend
PYTHONPATH=. alembic upgrade head
```

### Emergency Automated Rollback
If a deployment degrades service health or encounters unexpected runtime errors, trigger an automated rollback:

```bash
./scripts/deploy_rollback.sh previous
```

This script will:
1. Downgrade database schema by 1 revision (`alembic downgrade -1`).
2. Revert Docker containers to the previous stable release tag.
3. Poll health endpoint `/api/v1/health` until HTTP 200 operational status is verified.
