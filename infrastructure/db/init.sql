-- Insurance Reasoning Engine (IRE) Database Initialization Script
-- Implements Multi-tenant Database Isolation Strategies (Schema-per-Tenant & RLS)

CREATE DATABASE ire_tenant_db;
CREATE DATABASE ire_ingestion_db;
CREATE DATABASE ire_claim_db;
CREATE DATABASE ire_reasoning_db;
CREATE DATABASE ire_ai_agent_db;
CREATE DATABASE ire_audit_db;
CREATE DATABASE ire_notification_db;

-- Connect to Tenant DB
\c ire_tenant_db;

CREATE TABLE tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(128) UNIQUE NOT NULL,
    isolation_strategy VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PROVISIONING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Connect to Claim DB and configure Row-Level Security (RLS)
\c ire_claim_db;

CREATE TABLE claims (
    claim_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    external_ref VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    payload JSONB NOT NULL,
    adjudication_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactional Outbox Table for Event Driven Architecture
CREATE TABLE outbox_events (
    id VARCHAR(64) PRIMARY KEY,
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) DEFAULT 'PENDING'
);

-- Enable RLS for Multi-Tenant Security
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_policy ON claims
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Connect to Audit Ledger DB
\c ire_audit_db;

CREATE TABLE audit_ledger (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    actor_id VARCHAR(64) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource VARCHAR(64) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    payload JSONB NOT NULL
);

CREATE INDEX idx_audit_tenant_resource ON audit_ledger(tenant_id, resource, resource_id);
