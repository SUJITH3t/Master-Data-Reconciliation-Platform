-- =======================================================================
-- Master Data Hub: Enterprise Clustered PostgreSQL / Amazon RDS Schema DDL
-- Compatible with PostgreSQL 14+, PgBouncer, Read Replicas & High Availability
-- =======================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Organizations (Multi-tenant partition)
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users & RBAC
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(64) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

-- 3. Source Systems
CREATE TABLE IF NOT EXISTS source_systems (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    priority_score INTEGER DEFAULT 5,
    authoritative_fields TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Golden Master Customers
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(128) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(64),
    address TEXT,
    verification_status VARCHAR(64) DEFAULT 'Unverified',
    data_quality_score DOUBLE PRECISION DEFAULT 100.0,
    status VARCHAR(64) DEFAULT 'Active',
    last_reconciled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_biz ON customers(business_id);
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- 5. Golden Master Products
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(128) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    sku VARCHAR(128),
    name VARCHAR(255),
    category VARCHAR(128),
    price DOUBLE PRECISION,
    status VARCHAR(64) DEFAULT 'Active',
    verification_status VARCHAR(64) DEFAULT 'Unverified',
    data_quality_score DOUBLE PRECISION DEFAULT 100.0,
    last_reconciled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);

-- 6. Golden Master Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    business_id VARCHAR(128) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(64),
    address TEXT,
    compliance_status VARCHAR(64) DEFAULT 'Compliant',
    verification_status VARCHAR(64) DEFAULT 'Unverified',
    data_quality_score DOUBLE PRECISION DEFAULT 100.0,
    last_reconciled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id)
);

-- 7. Raw Source System Feed Records
CREATE TABLE IF NOT EXISTS source_records (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(64) NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    source_system VARCHAR(64) NOT NULL,
    business_identifier VARCHAR(128) NOT NULL,
    field_values JSONB NOT NULL,
    verification_status VARCHAR(64) DEFAULT 'Unverified',
    source_timestamp TIMESTAMP WITH TIME ZONE,
    reconciliation_status VARCHAR(64) DEFAULT 'PENDING',
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_records_biz ON source_records(business_identifier, record_type);
CREATE INDEX IF NOT EXISTS idx_source_records_status ON source_records(reconciliation_status);

-- 8. Reconciliation Cases & Governance Lifecycle
CREATE TABLE IF NOT EXISTS reconciliation_cases (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(128) UNIQUE NOT NULL,
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    record_type VARCHAR(64) NOT NULL,
    business_id VARCHAR(128) NOT NULL,
    attribute_name VARCHAR(128) NOT NULL,
    recommended_value TEXT,
    recommended_source VARCHAR(64),
    confidence_score DOUBLE PRECISION,
    confidence_tier VARCHAR(32),
    rationale TEXT,
    status VARCHAR(64) DEFAULT 'PENDING',
    manual_review_required INTEGER DEFAULT 0,
    conflict_detected INTEGER DEFAULT 0,
    source_values_snapshot JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recon_cases_status ON reconciliation_cases(status);
CREATE INDEX IF NOT EXISTS idx_recon_cases_biz ON reconciliation_cases(business_id);

-- 9. Approvals & Governance Actions
CREATE TABLE IF NOT EXISTS approvals (
    id SERIAL PRIMARY KEY,
    case_id INTEGER NOT NULL REFERENCES reconciliation_cases(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    decision VARCHAR(64) NOT NULL,
    rejection_reason TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. Immutable Audit Trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(128) UNIQUE NOT NULL,
    action VARCHAR(128) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    organization_id INTEGER NOT NULL REFERENCES organizations(id),
    record_type VARCHAR(64),
    business_id VARCHAR(128),
    decision VARCHAR(64),
    reason TEXT,
    field_changed VARCHAR(128),
    old_value TEXT,
    new_value TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_biz ON audit_logs(business_id);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp);

-- 11. Probabilistic Linkage Pairs & Clusters
CREATE TABLE IF NOT EXISTS probabilistic_linkage_pairs (
    id SERIAL PRIMARY KEY,
    record_type VARCHAR(64) NOT NULL,
    source_a_system VARCHAR(64) NOT NULL,
    source_a_id VARCHAR(128) NOT NULL,
    source_b_system VARCHAR(64) NOT NULL,
    source_b_id VARCHAR(128) NOT NULL,
    fellegi_sunter_weight DOUBLE PRECISION NOT NULL,
    cosine_similarity DOUBLE PRECISION NOT NULL,
    jaro_winkler_similarity DOUBLE PRECISION NOT NULL,
    classification VARCHAR(64) NOT NULL, -- 'DEFINITE_MATCH', 'POSSIBLE_MATCH', 'NON_MATCH'
    comparison_details JSONB,
    reviewed INTEGER DEFAULT 0,
    resolved_golden_id VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_linkage_class ON probabilistic_linkage_pairs(classification);

-- 12. Asynchronous Streaming Ingestion Logs & CDC Events
CREATE TABLE IF NOT EXISTS streaming_cdc_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(128) UNIQUE NOT NULL,
    connector VARCHAR(64) NOT NULL,
    table_name VARCHAR(64) NOT NULL,
    operation VARCHAR(16) NOT NULL, -- 'c', 'u', 'd', 'r'
    payload JSONB NOT NULL,
    lag_ms DOUBLE PRECISION DEFAULT 0.0,
    processed_status VARCHAR(64) DEFAULT 'PROCESSED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
