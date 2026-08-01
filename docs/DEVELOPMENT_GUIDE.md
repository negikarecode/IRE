# Development Guide

This guide provides instructions for setting up the **Insurance Reasoning Engine (IRE)** development environment.

## Prerequisites

- **Node.js**: v20+
- **pnpm**: v9+
- **Python**: v3.11+
- **Docker & Docker Compose**

## Local Setup

### 1. TypeScript Monorepo Microservices

```bash
cd /home/aryan/Videos/IRE
pnpm install
pnpm build
```

To run a specific service in development mode:

```bash
cd services/claim-lifecycle-service
pnpm dev
```

### 2. Python FastAPI Backend

```bash
cd /home/aryan/Videos/IRE/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Running Tests

### Microservices TypeScript Tests

```bash
pnpm test
```

### Python Backend Tests

```bash
cd backend
python3 -m py_compile app/main.py
```
