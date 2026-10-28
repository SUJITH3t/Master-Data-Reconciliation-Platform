"""Database Schema Definitions for Master Data Hub."""

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL, -- 'Store Manager', 'Reconciliation Specialist', 'Admin', 'External Partner'
    organization_id INTEGER NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS source_systems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    priority_score INTEGER DEFAULT 5,
    authoritative_fields TEXT, -- comma-separated fields
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    verification_status TEXT DEFAULT 'Unverified',
    data_quality_score REAL DEFAULT 100.0,
    status TEXT DEFAULT 'Active',
    last_reconciled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    sku TEXT,
    name TEXT,
    price REAL,
    category TEXT,
    status TEXT DEFAULT 'Active',
    data_quality_score REAL DEFAULT 100.0,
    last_reconciled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    name TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    status TEXT DEFAULT 'Active',
    verification_status TEXT DEFAULT 'Unverified',
    data_quality_score REAL DEFAULT 100.0,
    last_reconciled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(business_id, organization_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS source_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL, -- Customer, Product, Supplier
    organization_id INTEGER NOT NULL,
    source_system TEXT NOT NULL,
    business_identifier TEXT NOT NULL,
    field_values_json TEXT NOT NULL,
    verification_status TEXT DEFAULT 'Unverified',
    source_timestamp TIMESTAMP NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS reconciliation_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT UNIQUE NOT NULL,
    record_type TEXT NOT NULL,
    business_id TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    issue_type TEXT NOT NULL, -- Conflict, Missing, Stale, Verification Mismatch
    recommended_value TEXT,
    winning_source TEXT,
    previous_value TEXT,
    confidence_score REAL,
    status TEXT DEFAULT 'PENDING', -- PENDING, IN_REVIEW, APPROVED, PUBLISHED, REJECTED, MANUAL_REVIEW
    reason TEXT,
    explanation TEXT,
    evidence_json TEXT,
    reviewer_id INTEGER,
    reviewer_notes TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS reconciliation_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    decision TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    reason TEXT,
    previous_status TEXT,
    new_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES reconciliation_cases(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS survivorship_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    field_name TEXT NOT NULL,
    rule_definition_json TEXT NOT NULL,
    description TEXT,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    business_id TEXT NOT NULL,
    organization_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    winning_source TEXT,
    user_id INTEGER,
    user_email TEXT,
    reason TEXT,
    reconciliation_case_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (reconciliation_case_id) REFERENCES reconciliation_cases(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    user_email TEXT,
    role TEXT,
    organization_id INTEGER,
    action TEXT NOT NULL,
    record_type TEXT,
    business_id TEXT,
    decision TEXT,
    reason TEXT,
    ip_address TEXT DEFAULT '127.0.0.1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS validation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    engine_name TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    total_records INTEGER NOT NULL,
    precision_score REAL NOT NULL,
    false_positive_rate REAL NOT NULL,
    success_rate REAL NOT NULL,
    manual_review_rate REAL NOT NULL,
    avg_processing_time_ms REAL NOT NULL,
    total_processing_time_s REAL NOT NULL,
    correct_count INTEGER NOT NULL,
    incorrect_count INTEGER NOT NULL,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS probabilistic_linkage_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    source_a_system TEXT NOT NULL,
    source_a_id TEXT NOT NULL,
    source_b_system TEXT NOT NULL,
    source_b_id TEXT NOT NULL,
    fellegi_sunter_weight REAL NOT NULL,
    cosine_similarity REAL NOT NULL,
    jaro_winkler_similarity REAL NOT NULL,
    classification TEXT NOT NULL,
    comparison_details TEXT,
    reviewed INTEGER DEFAULT 0,
    resolved_golden_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS streaming_cdc_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,
    connector TEXT NOT NULL,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    payload TEXT NOT NULL,
    lag_ms REAL DEFAULT 0.0,
    processed_status TEXT DEFAULT 'PROCESSED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance and isolation
CREATE INDEX IF NOT EXISTS idx_customers_org ON customers(organization_id);
CREATE INDEX IF NOT EXISTS idx_products_org ON products(organization_id);
CREATE INDEX IF NOT EXISTS idx_suppliers_org ON suppliers(organization_id);
CREATE INDEX IF NOT EXISTS idx_source_records_match ON source_records(record_type, organization_id, business_identifier);
CREATE INDEX IF NOT EXISTS idx_recon_cases_org ON reconciliation_cases(organization_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_change_history_record ON change_history(record_type, business_id);
CREATE INDEX IF NOT EXISTS idx_linkage_class ON probabilistic_linkage_pairs(classification);
"""
