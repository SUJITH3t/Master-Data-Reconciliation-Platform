# Master Data Reconciliation Platform (Master Data Hub)
## 35% Milestone Project Evaluation & Technical Architecture Report
**Submission Target:** Qbee AI Review & Evaluation Panel  
**Repository:** [https://github.com/SUJITH3t/Master-Data-Reconciliation-Platform.git](https://github.com/SUJITH3t/Master-Data-Reconciliation-Platform.git)  
**Author / Developer:** Sujith Kumar (`SUJITH3t` / `sujith.eai24@rathinam.in`)  
**Commit Reference:** `333b31d8ccf62acad8325a4d16a38c6809ce938b` (`origin/main`)  
**Evaluation Status:** Phase 1 Complete (100% Core Engine, Functional UI, 13/13 Passing Automated Tests, 20/20 Quality Gates Verified)

---

## 1. Executive Summary & Problem Formulation

### 1.1 Business Problem Context
In modern retail enterprises, core business entities—**Customers**, **Products**, and **Suppliers**—are ingested continuously from disparate operational systems, including Enterprise Resource Planning (ERP), E-commerce digital storefronts, Point-of-Sale (POS) physical store inventories, and third-party delivery/dispatch partners. 

Because these operational nodes operate asynchronously without centralized consensus:
- **Conflicting Values:** Different systems report contradictory field values (e.g., legacy billing addresses vs. recent shipping addresses).
- **Data Freshness Decay:** Records contain stale, unmaintained values alongside freshly modified records.
- **Incomplete Records:** Upstream systems omit mandatory attributes (e.g., POS lacks customer emails).
- **Verification Discrepancies:** Systems carry unverified assertions that clash with officially verified records.
- **High Operational Latency:** Manual side-by-side comparison across tabular interfaces is slow, costly, error-prone, and cannot scale to enterprise volumes.

### 1.2 The Master Data Hub Solution
**Master Data Hub** is an end-to-end, deterministic master data reconciliation platform. It replaces arbitrary heuristics and opaque manual intervention with an auditable, rule-driven, explainable, and human-supervised reconciliation pipeline. It features:
1. Deterministic entity normalization and matching.
2. Configurable time-decay freshness scoring.
3. YAML-driven deterministic survivorship rule execution.
4. An **Ambiguity Safety Catch** that halts and routes ties to human review rather than making unsafe guesses.
5. Mathematical confidence scoring (0–100%).
6. Plain-English, business-readable explanations.
7. Enterprise governance workflows (`PENDING` &rarr; `APPROVED` &rarr; `PUBLISHED` / `REJECTED` / `MANUAL_REVIEW`).
8. Organization-level data isolation and multi-role RBAC.

---

## 2. System Architecture & High-Level Design

### 2.1 Multi-Layer Architecture
The platform is designed with clean architectural separation across six distinct tiers:

```mermaid
graph TD
    subgraph UI_Layer["1. Presentation Tier (Streamlit Enterprise UI)"]
        UI_DASH[Master Data Health Dashboard]
        UI_RECON[Reconciliation Workspace]
        UI_QUEUE[Approval Queue]
        UI_REC[Master Records Catalog]
        UI_VAL[Validation & Performance Benchmark]
        UI_HIST[Change History Timeline]
        UI_AUDIT[Immutable Audit Log]
        UI_ADMIN[Administration & Rule Editor]
    end

    subgraph App_Layer["2. Business & Service Layer"]
        SVC_AUTH[Auth & RBAC Service]
        SVC_REC[Master Record Service]
        SVC_APP[Approval & Governance Service]
        SVC_AUD[Audit Service]
        SVC_HIST[History Service]
        SVC_VAL[Validation Benchmark Service]
        SVC_LLM[Groq Explanation Refiner Stub]
    end

    subgraph Engine_Layer["3. Reconciliation & Survivorship Engine Core"]
        ENG_MATCH[Deterministic Normalization & Matching]
        ENG_FRESH[Freshness Evaluator (<=30d Fresh, >30d Stale)]
        ENG_RULES[Dynamic YAML Survivorship Rule Engine]
        ENG_CONF[Confidence Scorer (0-100%)]
        ENG_EXPL[Plain-English Explainer]
        ENG_SAFE{Ambiguity Tie?}
        ENG_BASE[Naive Baseline Engine]
    end

    subgraph Data_Layer["4. Persistence Tier (SQLite + Schema)"]
        DB[(master_data.db)]
        T_ORGS[organizations]
        T_USERS[users]
        T_SRCS[source_systems]
        T_MAST[customers / products / suppliers]
        T_RECS[source_records]
        T_CASES[reconciliation_cases]
        T_DECS[reconciliation_decisions]
        T_HIST[change_history]
        T_AUD[audit_logs]
        T_VAL[validation_results]
    end

    subgraph API_Layer["5. Headless Integration Tier (FastAPI)"]
        API_INGEST[POST /api/records/ingest]
        API_PENDING[GET /api/reconciliation/pending]
        API_CASE[GET /api/reconciliation/{id}]
        API_APPROVE[POST /api/reconciliation/{id}/approve]
        API_REJECT[POST /api/reconciliation/{id}/reject]
        API_BATCH[POST /api/reconciliation/batch]
        API_AUDIT[GET /api/audit/{id}]
    end

    UI_Layer <--> App_Layer
    API_Layer <--> App_Layer
    App_Layer <--> Engine_Layer
    App_Layer <--> Data_Layer
    Engine_Layer --> ENG_SAFE
    ENG_SAFE -- "Tie Detected" --> SVC_APP
    ENG_SAFE -- "Clear Winner" --> ENG_CONF --> ENG_EXPL --> SVC_APP
```

### 2.2 Ingestion & Reconciliation Pipeline Sequence
1. **Source Ingestion:** Records enter from ERP, E-commerce, POS, or Delivery Partner with raw timestamps and verification tags.
2. **Deterministic Normalization:** Strings are trimmed, case-normalized, phone numbers stripped to digits, emails validated, and SKUs standardized.
3. **Identity Clustering:** Records are deterministically clustered by `business_id` (or normalized unique keys).
4. **Freshness & Staleness Calculation:** Timestamps are computed relative to reference time:
   $$\text{Age (days)} = \frac{t_{\text{ref}} - t_{\text{source}}}{86400}$$
   - $0 \le \text{Age} \le 30 \implies \text{Fresh}$
   - $\text{Age} > 30 \implies \text{Stale}$
   - Value is empty $\implies \text{Missing}$
5. **Survivorship Rule Execution:** Candidate values are scored dynamically against rules in `config/survivorship_rules.yaml`.
6. **Ambiguity Safety Check:** If two distinct non-empty values have identical top scores and no rule can break the tie, the system executes a **Safety Halt** and routes the record to `MANUAL_REVIEW`.
7. **Mathematical Confidence Calculation:**
   $$\text{Confidence} = w_{\text{ver}} + w_{\text{fresh}} + w_{\text{auth}} + w_{\text{agree}} + w_{\text{comp}} - \text{penalty}$$
8. **Plain-English Explanation:** Deterministic narrative generated detailing winner, losing candidates, and missing systems.
9. **Decision & Persistence:** Workflow updates SQLite, writes to immutable change history, and records an audit log event.

---

## 3. Code Commit & Repository Audit

- **Repository:** `https://github.com/SUJITH3t/Master-Data-Reconciliation-Platform.git`
- **Initial Commit Hash:** `333b31d8ccf62acad8325a4d16a38c6809ce938b`
- **Branch:** `main` (synchronized with `origin/main`)
- **Total Files Tracked:** 50 files
- **Total Lines of Code:** 5,923 lines
- **No Third-Party Frontend Frameworks:** 100% Python, Streamlit, Pandas, Plotly, SQLite, FastAPI, PyYAML.

---

## 4. Comprehensive Component Breakdown

| Component Path | Technical Module | Role & Implementation Details |
| :--- | :--- | :--- |
| `database/schema.py` | Schema & DDL | Defines 13 SQLite tables with foreign key cascades, unique constraints, and B-tree indexes for fast org-filtered retrieval. |
| `database/database.py` | Connection Manager | Handles atomic transactions, SQLite WAL mode, parameterization against SQL injection, and row-factory mapping. |
| `database/seed.py` | Data Seeder | Automatically bootstraps 3 organizations, 4 demo users, 4 source systems, 50 master entities, 690 raw source fields, and pre-computed cases on first startup. |
| `config/survivorship_rules.yaml` | Rule Configuration | Declarative YAML defining field-specific survivorship logic (Customer email/phone/address, Product price/status/sku, Supplier status/email). |
| `engine/matching.py` | Normalizer & Matcher | Alphanumeric cleansing, whitespace collapsing, phone standardization, email syntax check, and deterministic entity clustering. |
| `engine/freshness.py` | Freshness Evaluator | Evaluates age in days, flags `Fresh` vs `Stale` vs `Missing`, and formats human-readable relative time badges. |
| `engine/survivorship.py` | Survivorship Core | Dynamic evaluator of verification, recency, source priority, and validity. Contains strict ambiguity tie-breaking logic. |
| `engine/confidence.py` | Confidence Scorer | Verifiable mathematical confidence formula yielding 0–100% confidence tiers (High &ge;90%, Medium 70–89%, Low <70%). |
| `engine/explanation.py` | Business Explainer | Formulates clear, plain-English justifications (e.g., *"The e-commerce email was selected because it is verified and was updated more recently than the ERP value"*). |
| `engine/baseline.py` | Naive Baseline | Fixed-priority / first non-null baseline algorithm used for empirical benchmarking against the proposed engine. |
| `engine/reconciliation.py` | Pipeline Orchestrator | Ties matching, freshness, survivorship, confidence, and explanation into an atomic, deterministic field processing pipeline. |
| `services/auth_service.py` | RBAC & Security | Password hashing, permission enforcement for 4 roles, and multi-tenant organization boundary verification. |
| `services/record_service.py` | Entity Catalog Service | Master records and raw source records CRUD operations with mandatory org-level query filtering. |
| `services/approval_service.py` | Governance State Machine | Governs transitions (`PENDING`, `APPROVED`, `PUBLISHED`, `REJECTED`, `MANUAL_REVIEW`) and batch reconciliation execution. |
| `services/audit_service.py` | Audit Logging | Immutable audit trail capturing timestamp, user ID, role, action, target record, decision, reason, and IP address. |
| `services/history_service.py` | Lineage Service | Tracks field-level historical transitions (`previous_value` &rarr; `new_value`, winning source, approver, case number). |
| `services/validation_service.py` | Benchmark Engine | Scientific comparison engine evaluating 50+ master records against expected ground truth; computes precision, FPR, and latency. |
| `services/llm_service.py` | Optional Groq AI | Safe LLM bridge using `GROQ_API_KEY` to refine wording while architecturally preventing the LLM from choosing winners. |
| `api/routes.py` | REST API | FastAPI headless endpoints for programmatic ingestion, case inspection, approval, rejection, and audit extraction. |
| `ui/styles.py` & `components.py` | Design System | Enterprise CSS design tokens, responsive KPI cards, status badge pills, and side-by-side source matrix cards. |
| `ui/dashboard.py` | Executive Dashboard | Master Data Health KPI metrics, data health counters (Fresh, Stale, Missing, Conflicts), and interactive Plotly charts. |
| `ui/reconciliation.py` | Reconciliation Workspace | Dual-pane case browser with side-by-side system comparison, prominent recommendation cards, and evidence expanders. |
| `ui/approvals.py` | Governance Queue | Tabular workflow queue for one-click approval, rejection (with mandatory justification), and manual review escalation. |
| `ui/records.py` | Master Catalog | Searchable directory of Customers, Products, and Suppliers with data quality indicators and full source-record inspectability. |
| `ui/validation.py` | Scientific Benchmark UI | Comparative metric table (Baseline vs Proposed vs Target), error analysis expander, and 3 interactive edge case runners. |
| `ui/history.py` | Change History | Visual chronological audit trail showing master record field changes and lineage. |
| `ui/audit.py` | Audit Log Viewer | Admin-only security audit browser with multi-parameter filtering. |
| `ui/admin.py` | Governance Console | User account provisioning, organization viewer, and live YAML survivorship rules editor. |

---

## 5. Requirements Satisfaction Matrix

The following matrix documents how the requirements specified for evaluation were satisfied:

| Spec Requirement | Evaluation Criteria | Implementation Mechanism | Verification Result |
| :--- | :--- | :--- | :--- |
| **1. Primary Objective** | Normalize, detect differences, stale, missing, survivorship, confidence, plain-English explanations. | `engine/reconciliation.py`, `survivorship.py`, `explanation.py` | ✅ **Fully Satisfied**: Processes 4 source systems, extracts differences, applies YAML rules, and outputs plain-English reasons. |
| **2. Non-Negotiable Tech** | Python, Streamlit, Pandas, SQLite, Plotly, YAML, FastAPI, python-dotenv, optional Groq. | Core stack built strictly without React, Angular, or external frontends. | ✅ **Fully Satisfied**: Starts with `streamlit run app.py` and API with `uvicorn api.routes:app`. |
| **4. Business-Friendly UI** | Business language everywhere; no raw SQL, code traces, or cryptic rule IDs. | `ui/styles.py`, `ui/components.py`, `engine/explanation.py` | ✅ **Fully Satisfied**: Standardized status badges (`🟢 Fresh`, `⚠️ Conflict`, `👤 Manual Review`), clear KPI cards. |
| **7 & 8. Login & Demo Mode** | Functional sign-in + 1-click demo personas (Admin, Specialist, Manager, Partner). | `ui/login.py`, `services/auth_service.py` | ✅ **Fully Satisfied**: 4 realistic demo users pre-seeded with documented credentials. |
| **9 & 10. RBAC & Org Isolation** | Backend-enforced permissions and organization-level data partitioning. | `services/auth_service.py`, `services/record_service.py` | ✅ **Fully Satisfied**: External Partner strictly restricted to Delivery Partner org; unauthorized actions rejected. |
| **11-14. Live Dashboard** | KPI cards and charts calculated from real database, not hard-coded. | `ui/dashboard.py` | ✅ **Fully Satisfied**: Dynamic SQL queries count total records, needs attention, pending, manual reviews, and health breakdown. |
| **18-24. Reconciliation Engine** | Deterministic pipeline, YAML rules, freshness threshold, and ambiguity safety. | `engine/reconciliation.py`, `engine/survivorship.py` | ✅ **Fully Satisfied**: Tie cases automatically route to `MANUAL_REVIEW` without guessing. |
| **25. Confidence Scoring** | Calculated mathematically from verification, freshness, authority, agreement. | `engine/confidence.py` | ✅ **Fully Satisfied**: Verifiable formula outputting High (&ge;90%), Medium (70-89%), and Low (<70%). |
| **28. Groq LLM Boundary** | Optional Groq integration for narrative only; LLM never decides winning values. | `services/llm_service.py` | ✅ **Fully Satisfied**: Runs 100% offline without key; if enabled, only refines deterministic text. |
| **34-38. Approval & Publishing** | `PENDING` &rarr; `APPROVED` &rarr; `PUBLISHED`; rejection requires reason; master table updated. | `services/approval_service.py` | ✅ **Fully Satisfied**: Real SQLite updates to master tables, change history, and audit log. |
| **42-49. Validation & Benchmark** | 50+ master records, baseline vs proposed engine, precision, FPR, latency, error analysis, edge cases. | `services/validation_service.py`, `ui/validation.py` | ✅ **Fully Satisfied**: Empirical benchmark on 50 entities; 3 interactive edge case tests pass. |
| **50. API Integration Stubs** | Ingest, pending, approve, reject, batch, audit REST endpoints. | `api/routes.py` (FastAPI) | ✅ **Fully Satisfied**: Endpoints share identical service and database layer. |
| **65-69. Automated Testing** | Critical email conflict, ambiguous tie, permission matrix, persistence, validation metrics. | `tests/` test suite (Pytest) | ✅ **Fully Satisfied**: 13/13 unit and integration tests passing. |

---

## 6. Empirical Validation Benchmark & Results

The validation engine executed the complete 50-entity dataset (690 source fields across Customers, Products, and Suppliers) through both the naive Baseline and the Proposed Reconciliation Engine:

```
=================================================================================================
                                VALIDATION BENCHMARK RESULTS
=================================================================================================
Metric                       Baseline (Fixed Priority)   Proposed Dynamic Engine   Target Status
-------------------------------------------------------------------------------------------------
Precision Score              22.0%                       100.0%                    ✅ Achieved (>= 90%)
False Positive Rate (FPR)    78.0%                       0.0%                      ✅ Achieved (<= 5%)
Reconciliation Success Rate  22.0%                       100.0%                    ✅ Achieved (>= 90%)
Manual Review Escalation     0.0% (Unsafe Resolution)    10.0% (Safety Halt)       ✅ Achieved (<= 15%)
Average Processing Latency   0.002 ms                    0.084 ms                  ✅ Achieved (<= 10ms)
Total Processing Duration    0.0011 s                    0.0042 s                  Fast & Lightweight
=================================================================================================
```

### Why Baseline Failed (78% False Positive Rate):
1. **Ignored Verification:** Baseline routinely selected unverified store inputs over verified e-commerce values simply because store was listed earlier.
2. **Ignored Freshness:** Baseline chose 90-day-old stale values over records updated 1 day prior.
3. **Unsafe Resolution:** When two verified records had identical timestamps and conflicting values, Baseline picked one at random, whereas Proposed Engine safely halted and routed to `MANUAL_REVIEW`.

---

## 7. Quality Gate Verification (20/20 Passed)

The end-to-end automated quality gate harness (`verify_quality_gate.py`) verified all 20 lifecycle checkpoints:
1. **Database Schema Creation:** SQLite created with tables, foreign keys, and indexes.
2. **Database Seeding:** 3 organizations, 4 demo users, 4 source systems, 50 entities, 150 source record groups seeded.
3. **Authentication:** Store Manager, Reconciliation Specialist, Admin, and External Partner successfully login.
4. **Organization Data Isolation:** External Partner only views Delivery Partner records (`organization_id = 3`); unauthorized operations blocked.
5. **Batch Reconciliation Execution:** Processed 150 candidate fields with automatic resolutions and manual review routing.
6. **Case Inspection:** Side-by-side comparison displays accurate values, freshness badges, and verification tags.
7. **Approval Workflow:** Case `REC-CUS-CUST-019-ADDRESS` transitioned to `APPROVED`.
8. **Rejection Workflow:** Case `REC-CUS-CUST-020-PHONE` rejected with mandatory reason (`"Typo in candidate source"`).
9. **Manual Review Escalation:** Case `REC-CUS-CUST-020-ADDRESS` routed to `MANUAL_REVIEW` with reason.
10. **Publishing Workflow:** Approved case published to master `customers` table.
11. **Master Record Update:** Field value verified updated in SQLite.
12. **Change History Creation:** Historical record created with previous value, new value, winning source, approver.
13. **Audit Log Persistence:** Action logged with user email, timestamp, decision, and IP address.
14. **Validation Benchmark Execution:** Real metrics measured against ground truth dataset.
15. **Baseline Comparison:** Accurately calculates baseline deficiencies.
16. **Proposed Engine Execution:** Demonstrates 100% precision and 0% false positives.
17. **Edge Case 1 (All Disagree):** Evaluated and routed to `MANUAL_REVIEW`.
18. **Edge Case 2 (Stale vs Missing):** Evaluated and preserved stale value over missing.
19. **Edge Case 3 (Ambiguous Tie):** Evaluated and routed to `MANUAL_REVIEW`.
20. **Session Persistence Check:** State persists cleanly across session reloads and restarts.

---

## 8. Test Execution Evidence

All 13 automated tests executed via `pytest -v`:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/assujith/Documents/CoE_project_3
collected 13 items

tests/test_edge_cases.py::test_ambiguous_verified_email_tie PASSED       [  7%]
tests/test_edge_cases.py::test_stale_preserved_over_missing PASSED       [ 15%]
tests/test_edge_cases.py::test_edge_case_interactive_demonstrators PASSED [ 23%]
tests/test_permissions.py::test_rbac_permission_matrix PASSED            [ 30%]
tests/test_permissions.py::test_organization_data_isolation PASSED       [ 38%]
tests/test_permissions.py::test_unauthorized_operation_blocked PASSED    [ 46%]
tests/test_permissions.py::test_approval_and_publishing_persistence PASSED [ 53%]
tests/test_reconciliation.py::test_critical_customer_email_conflict PASSED [ 61%]
tests/test_reconciliation.py::test_unanimous_agreement PASSED            [ 69%]
tests/test_rules.py::test_yaml_config_loading PASSED                     [ 76%]
tests/test_rules.py::test_erp_product_status_priority PASSED             [ 84%]
tests/test_rules.py::test_verified_supplier_priority PASSED              [ 92%]
tests/test_validation.py::test_validation_benchmark_execution PASSED     [100%]

============================== 13 passed in 0.10s ==============================
```

---

## 9. Conclusion & Next Steps for 70% Milestone Review

The project has achieved **100% of its foundational architecture, core reconciliation engine, governance workflows, persistence, UI, API stubs, and validation benchmark requirements**. 

For the upcoming **70% review phase**, the planned milestones are:
1. **Asynchronous Streaming Ingestion:** Integrating Kafka/RabbitMQ consumer workers to support high-throughput streaming record streams.
2. **Probabilistic Linkage Layer:** Introducing Fellegi-Sunter / Cosine distance matching for phonetic and typographical entity clustering.
3. **Production Database Migration:** Containerization via Docker Compose with PostgreSQL backend and connection pooling.
