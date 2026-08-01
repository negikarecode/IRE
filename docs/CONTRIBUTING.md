# Contribution & Coding Style Guide

Thank you for contributing to the **Insurance Reasoning Engine (IRE)**.

## Core Directives

1. **Zero Hardcoded Domain Rules**: NEVER hardcode medical, clinical, or insurance rules in platform infrastructure. All rules must be written as declarative plugins or DSL expressions.
2. **Clean Architecture**: Maintain strict layer separation (`domain` → `application` → `infrastructure` → `presentation`).
3. **API-First**: Always define OpenAPI schemas or gRPC protobuf contracts before implementing new endpoints.
4. **Multi-Tenancy Context**: Ensure all database queries and async calls preserve tenant isolation via `X-Tenant-ID` and `tenant_id`.

## Branching & Pull Requests

- Use feature branches (`feature/add-connector-x`, `fix/issue-123`).
- Ensure `pnpm build` and `python3 -m py_compile` pass cleanly with zero errors before submitting a PR.
