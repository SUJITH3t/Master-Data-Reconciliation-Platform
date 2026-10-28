# Master Data Hub (Master Data Reconciliation Platform)

> **Reconcile and manage trusted customer, product, and supplier information across enterprise business systems.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-36%20Passed-brightgreen.svg)]()
[![Persistence](https://img.shields.io/badge/PostgreSQL-Clustered%20%2B%20PgBouncer-336791.svg)](https://www.postgresql.org/)
[![Security](https://img.shields.io/badge/Security-JWT%20Bearer%20Auth-red.svg)]()
[![Streaming](https://img.shields.io/badge/Streaming-Kafka%20%2B%20Debezium%20CDC-black.svg)]()
[![Linkage](https://img.shields.io/badge/Entity%20Linkage-Fellegi--Sunter-orange.svg)]()
[![Precision](https://img.shields.io/badge/Reconciliation%20Precision-100%25-success.svg)]()

---

## 1. Project Overview

**Master Data Hub** is a full-stack, enterprise-grade Master Data Reconciliation Platform designed for multi-channel retail organizations. It ingests master records (Customers, Products, Suppliers) across disparate operational systems (ERP, E-commerce, Store POS Network, Delivery Partner), automatically identifies discrepancies, missing attributes, stale records, and verification mismatches, and applies deterministic survivorship rules augmented with probabilistic entity linkage to recommend single golden master values.

### Key Capabilities:
- **Probabilistic Entity Linkage (Fellegi-Sunter):** Typo-tolerant matching using the classic Fellegi-Sunter (1969) model, Jaro-Winkler distance, Character 3-gram Cosine similarity, and Soundex phonetic blocking to reconcile phonetic spelling variations (e.g., "Jonathon Smith" vs "Johnathan Smyth") and address abbreviations.
- **Asynchronous Streaming Ingestion:** High-throughput event consumption supporting Apache Kafka and Debezium Change Data Capture (CDC) JSON envelopes (`op: c, u, d, r`), background daemon worker pools, sub-2ms enqueue latency, and streaming telemetry.
- **Production Clustered Persistence & Pooling:** Multi-backend abstraction supporting PostgreSQL 15 (Amazon RDS / Aurora) with `psycopg2.pool.ThreadedConnectionPool`, `SQLAlchemy` `QueuePool`, PgBouncer configuration, and automated SQLite migration with zero-config local fallback.
- **Hardened JWT Bearer Authentication:** RFC 7519 compliant JSON Web Token authentication using HMAC-SHA256 signatures, expiration rotation, and granular FastAPI role dependencies (`require_admin`, `require_specialist`).
- **W3C PROV-O Data Lineage & Provenance:** Full ontological DAG tracking (`prov:Entity`, `prov:Activity`, `prov:Agent`) establishing exact auditability for every golden master attribute.
- **Reviewer-Capacity Queuing Analysis:** Mathematical Erlang-C ($M/M/c$) queuing model determining required specialist FTE headcount, server utilization ($\rho$), queue wait times, and SLA compliance curves with cognitive fatigue bounds.
- **Deterministic Reconciliation Pipeline & Ambiguity Catch:** Dynamic YAML rules engine with a fail-safe ambiguity catch routing unresolvable ties to Human Review (`MANUAL_REVIEW`).
- **Mathematical Confidence Scoring:** 0–100% confidence calculated from verification status (+35%), timestamp freshness (+25%), source authority (+18%), multi-source agreement (+12%), and completeness (+10%).

---

## 2. Architecture Diagram (70% Milestone State)

```mermaid
graph TD
    subgraph Operational Feeds & Streaming
        S1[ERP SAP/Oracle]
        S2[E-commerce Shopify]
        S3[Store POS Network]
        S4[Delivery Partner Logistics]
        KAFKA[Kafka / Debezium CDC Broker]
        S1 & S2 & S3 & S4 --> KAFKA
    end

    subgraph Data Ingestion & Streaming Buffer Layer
        STREAM[Asynchronous Streaming Engine]
        QUEUE[Thread-Safe In-Memory Queue]
        WORKERS[Worker Pool Daemon Threads]
        KAFKA --> STREAM --> QUEUE --> WORKERS
    end

    subgraph Normalization & Probabilistic Linkage Core
        NORM[Normalization & Cleansing]
        SOUNDEX[Phonetic Soundex Blocking]
        FS_MODEL[Fellegi-Sunter Matcher]
        JW[Jaro-Winkler Typo Metric]
        COS[N-Gram Cosine Metric]
        
        WORKERS --> NORM --> SOUNDEX --> FS_MODEL
        FS_MODEL --- JW
        FS_MODEL --- COS
    end

    subgraph Reconciliation & Survivorship Engine
        R_RULES[Dynamic YAML Survivorship Rules]
        R_CONF[Confidence Scorer 0-100%]
        R_EXPL[Plain-English Explainer]
        R_SAFE{Ambiguous Tie?}
        
        FS_MODEL --> R_RULES --> R_SAFE
        R_SAFE -- "Yes (Tie / Borderline)" --> MR[Human Review Queue]
        R_SAFE -- "No (Clear Winner)" --> R_CONF --> R_EXPL --> REC[Reconciliation Recommendation]
    end

    subgraph Production Clustered Persistence Layer
        PGBOUNCER[PgBouncer Pooler]
        PG_DB[(PostgreSQL 15 / RDS)]
        SQLITE_DB[(SQLite WAL Fallback)]
        REC --> PGBOUNCER --> PG_DB
        MR --> PGBOUNCER --> PG_DB
        PG_DB -.-> SQLITE_DB
    end

    subgraph Governance, Lineage & Secure Delivery
        PROV[W3C PROV-O Lineage DAG Engine]
        CAPACITY[Erlang-C Queuing Simulator]
        API[FastAPI with JWT Bearer Auth]
        UI[Streamlit Enterprise Workspace]
        
        PG_DB <--> PROV
        MR <--> CAPACITY
        PG_DB <--> API
        PG_DB <--> UI
    end
```

---

## 3. Technology Stack

- **Core Application & Logic:** Python 3.10+, Pandas, Pydantic, Scikit-learn, SciPy
- **Probabilistic Entity Linkage:** Fellegi-Sunter (1969), Jaro-Winkler, N-gram Cosine, Soundex
- **Streaming Ingestion:** Debezium CDC JSON parser, asynchronous queue buffer, worker pools
- **API Security:** PyJWT (RFC 7519 HMAC-SHA256), OAuth2 Password Bearer
- **Production Persistence:** PostgreSQL 15, PgBouncer, `psycopg2` ThreadedConnectionPool, `SQLAlchemy` QueuePool
- **Queuing & Capacity:** Erlang-C ($M/M/c$) Multiserver Mathematical Model
- **Lineage Standard:** W3C PROV-O (Provenance Ontology)
- **Frontend / UI:** Streamlit (Custom Enterprise CSS, Glassmorphism Badges)
- **Visualizations:** Plotly Express & Plotly Graph Objects
- **Rule Configuration:** PyYAML (`config/survivorship_rules.yaml`)
- **Automated Testing:** Pytest (36/36 Passing Tests)

---

## 4. Demo Users & Credentials

The platform includes pre-seeded demonstration accounts covering all RBAC personas:

| Role | Email | Password | Organization | Scope & Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin@retail.demo` | `Admin123!` | Retail Company (HQ) | Full global governance, rule editor, pool monitor, all orgs, audit viewer |
| **Reconciliation Specialist** | `specialist@retail.demo` | `Spec123!` | Retail Company (HQ) | Review evidence, approve, reject, escalate manual reviews, capacity simulator |
| **Store Manager** | `manager@retail.demo` | `Store123!` | Store Network | Isolated to store records; approve store conflicts; no admin access |
| **External Partner** | `partner@delivery.demo` | `Partner123!` | Delivery Partner | Strictly isolated to Delivery Partner records; read-only inspection |

*Quick 1-Click login buttons are available on the sign-in screen.*

---

## 5. Quickstart & Installation

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <repository_url>
cd Master-Data-Reconciliation-Platform

python3 -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Environment Configuration (Optional)
```bash
cp .env.example .env
```
*(Runs 100% offline out-of-the-box. To connect to PostgreSQL or Kafka, set `DATABASE_URL` and `KAFKA_BOOTSTRAP_SERVERS` in `.env` or use Docker Compose).*

### Step 3: Run with Docker Compose (PostgreSQL + PgBouncer + Kafka + App)
```bash
docker-compose up -d
```

### Step 4: Run Locally with Streamlit
```bash
streamlit run app.py
```

---

## 6. Running Headless API with JWT Bearer Authentication

To launch the FastAPI REST service:
```bash
uvicorn api.routes:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### Available API Endpoints:
- `POST /api/auth/token`: OAuth2 password bearer token endpoint for Swagger UI login.
- `POST /api/auth/login`: JSON login endpoint returning signed JWT access token.
- `GET /api/auth/me`: Authenticated user profile and RBAC permissions.
- `POST /api/linkage/compare`: Fellegi-Sunter typo-tolerant pairwise record comparison.
- `GET /api/linkage/benchmark`: 4-case probabilistic accuracy benchmark.
- `POST /api/stream/debezium/cdc`: Ingest Debezium CDC payload with sub-2ms response.
- `POST /api/stream/simulate`: Trigger simulated real-time POS & Shopify CDC stream.
- `GET /api/stream/status`: Stream queue depth, ingestion lag, and throughput metrics.
- `GET /api/database/status`: PostgreSQL cluster readiness and connection pool metrics.
- `POST /api/records/ingest`: Ingest raw source system records (JWT secured).
- `GET /api/reconciliation/pending`: Retrieve pending reconciliation cases (JWT secured).
- `POST /api/reconciliation/{case_id}/approve`: Approve recommendation (Specialist/Admin).
- `POST /api/reconciliation/{case_id}/reject`: Reject recommendation (Specialist/Admin).
- `GET /api/audit/{record_id}`: Retrieve audit history for a master record (JWT secured).

---

## 7. Running the Automated Test Suite (36/36 Passing)

To run all unit, security, linkage, streaming, edge-case, and validation tests:
```bash
pytest -v
```

### Test Suite Structure (36 Tests):
1. `tests/test_jwt_security.py` (6 tests): Token creation, cryptographic signature checks, expiration rejection, `/api/auth/login`, and RBAC enforcement.
2. `tests/test_probabilistic_linkage.py` (7 tests): Soundex blocking, Jaro-Winkler, N-gram Cosine, Fellegi-Sunter weights, and 100% benchmark.
3. `tests/test_streaming_ingestion.py` (3 tests): Debezium CDC parser (`c`, `u`), streaming queue enqueue, and worker telemetry.
4. `tests/test_postgres_persistence.py` (4 tests): PersistenceManager pool initialization, diagnostics, table discovery, and pooled queries.
5. `tests/test_lineage_and_capacity.py` (3 tests): W3C PROV-O DAG generation, Erlang-C stability, and capacity matrix.
6. `tests/test_reconciliation.py` (2 tests): Critical email conflict resolution and unanimous agreement.
7. `tests/test_rules.py` (3 tests): YAML configuration, ERP status priority, and supplier verification precedence.
8. `tests/test_permissions.py` (4 tests): Multi-tenant RBAC matrix, organization isolation, and approval persistence.
9. `tests/test_edge_cases.py` (3 tests): Ambiguous verified tie, stale vs missing preservation, and edge demonstrators.
10. `tests/test_validation.py` (1 test): 50-entity comparative validation benchmark.

---

## 8. Empirical Validation Methodology

The platform includes a real validation dataset of 50 master entities (20 Customers, 15 Products, 15 Suppliers) with 690 contributing source records in `data/validation_dataset.csv`.

### Benchmark Results:
| Metric | Baseline (Fixed Priority) | Proposed Dynamic Engine | Target | Result |
| :--- | :--- | :--- | :--- | :--- |
| **Precision** | 22.0% | **100.0%** | &ge; 90.0% | ✅ Achieved |
| **False Positive Rate** | 78.0% | **0.0%** | &le; 5.0% | ✅ Achieved |
| **Success Rate** | 22.0% | **100.0%** | &ge; 90.0% | ✅ Achieved |
| **Manual Review Rate** | 0.0% *(Unsafe)* | **10.0%** *(Safety Halt)* | &le; 15.0% | ✅ Achieved |
| **Avg Latency** | 0.002 ms | **0.084 ms** | &le; 10.0 ms | ✅ Achieved |

---

## 9. Comprehensive Documentation & Reports
- **70% Milestone Comprehensive Project Evaluation Report:** [`reports/project_evaluation_report_70_percent.md`](reports/project_evaluation_report_70_percent.md)
- **Formal Data Lineage & Reviewer-Capacity Analysis:** [`reports/lineage_and_capacity_analysis.md`](reports/lineage_and_capacity_analysis.md)
- **Prototype Limitations & Production Architecture:** [`reports/limitations.md`](reports/limitations.md)
- **Detailed Business & Functional Requirements:** [`reports/requirements.md`](reports/requirements.md)
