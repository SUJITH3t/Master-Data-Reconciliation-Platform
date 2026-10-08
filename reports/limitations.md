# Master Data Reconciliation Platform: Prototype Limitations & Production Roadmap

**Document Status:** Evaluation & Architectural Gap Analysis  
**Product:** Master Data Hub  

> [!WARNING]
> **Prototype Scope Notice:**  
> This prototype demonstrates the end-to-end reconciliation workflow, deterministic survivorship rule execution, mathematical confidence scoring, and multi-tenant organization isolation. However, it is an evaluation prototype and would require enterprise identity management, encryption at rest/in transit, secrets management, distributed monitoring, high availability, and production-grade database infrastructure before live enterprise deployment.

---

## 1. Architectural & Scalability Limitations

### 1.1 SQLite Persistence
- **Current Implementation:** Built on embedded SQLite (`master_data.db`) with Write-Ahead Logging (WAL) and foreign keys enabled.
- **Limitation:** SQLite is single-writer. In an enterprise retail environment receiving tens of thousands of POS transactions and e-commerce webhooks concurrently, database lock contention would throttle ingestion throughput.
- **Production Requirement:** Migrate persistence to a clustered enterprise relational database such as PostgreSQL (Amazon RDS / Aurora) or distributed SQL (CockroachDB) with connection pooling (PgBouncer) and read replicas.

### 1.2 Deterministic Matching vs. Probabilistic Record Linkage
- **Current Implementation:** Relies on deterministic exact matching on normalized primary keys (`business_id`, normalized email, normalized phone, formatted SKU).
- **Limitation:** Inability to reconcile customer entities when names have severe typographic errors, phonetic variations ("Jonathon Smith" vs "Johnathan Smyth"), or shifted house addresses without a shared phone/email.
- **Production Requirement:** Augment deterministic matching with a probabilistic Fellegi-Sunter record linkage model or vector embeddings with cosine similarity thresholds, backed by human-in-the-loop review for border scores (e.g., 0.75 - 0.88).

---

## 2. Security, Authentication & Compliance

### 2.1 Authentication & Session Management
- **Current Implementation:** In-memory session state with SHA-256 hashed password verification and 1-click role demo profiles.
- **Limitation:** Does not integrate with corporate Single Sign-On (SSO), SAML 2.0, Okta, Microsoft Entra ID, or OAuth2/OIDC. Session tokens are not signed JWTs with expiration rotation.
- **Production Requirement:** Implement an API Gateway with OAuth2/OIDC token validation, mTLS between internal services, and enterprise RBAC/ABAC role sync.

### 2.2 Data Encryption & Data Privacy (GDPR / CCPA)
- **Current Implementation:** Data fields (e.g., customer emails, phone numbers, home addresses) are stored in plaintext within SQLite.
- **Limitation:** Master customer data is PII (Personally Identifiable Information). Storing plaintext PII risks non-compliance with GDPR, CCPA, and PCI-DSS.
- **Production Requirement:** Enforce field-level encryption (Envelope Encryption via AWS KMS / HashiCorp Vault) and automated Right-to-be-Forgotten / Right-to-Erasure workflows.

---

## 3. Human Review & Rule Orchestration Limitations

### 3.1 Ambiguous & Cyclic Survivorship Rules
- **Current Implementation:** Dynamic YAML rules engine with fallback tie-breakers and an ambiguity safety catch routing unresolvable ties to `MANUAL_REVIEW`.
- **Limitation:** The current engine does not perform static cycle detection on complex chained graph rules (e.g., Rule A depends on Rule B which depends on Rule A).
- **Production Requirement:** Implement a Directed Acyclic Graph (DAG) validator to verify rule configurations at deploy time and prevent circular dependency conditions.

### 3.2 Machine Learning & LLM Boundary
- **Current Implementation:** Groq LLM integration is strictly restricted to narrative explanation polishing; it is architecturally prohibited from selecting winning values.
- **Limitation:** LLMs cannot autonomously adapt survivorship rules based on historical human approval patterns.
- **Production Requirement:** Introduce an active learning feedback loop that analyzes historical reconciliation specialist decisions to suggest rule parameter optimizations.

---

## 4. REST API & Integration Limitations
- **Current Implementation:** FastAPI stub endpoints (`/api/records/ingest`, `/api/reconciliation/*`) sharing the same core service layer.
- **Limitation:** Does not include asynchronous message brokers (Apache Kafka, RabbitMQ) or distributed task queues (Celery / Redis) for high-volume streaming record ingestion.
- **Production Requirement:** Deploy a streaming event consumer architecture (Kafka & Debezium CDC) feeding a microservice reconciliation worker pool.
