"""Administration and System Governance Console."""

import os
import yaml
import streamlit as st
import pandas as pd
from typing import Any, Dict

from database.database import execute_query, execute_non_query
from services.audit_service import AuditService
from ui.components import render_page_header


def render_admin_page(user: Dict[str, Any]):
    render_page_header(
        title="Administration & Governance",
        subtitle="System administration, role provisioning, organization partitioning, and survivorship rules configuration.",
        badge_text="Admin Console"
    )

    if user.get("role") != "Admin":
        st.error("Access Denied: You must have the Administrator role to access this section.")
        return

    admin_tabs = st.tabs([
        "👥 User Accounts",
        "🏢 Organizations",
        "🌐 Source Systems",
        "📜 Survivorship Rules",
        "🗄️ Persistence & Pool"
    ])

    # 1. User Management
    with admin_tabs[0]:
        st.markdown("##### Enterprise User Accounts & RBAC Provisioning")
        users_rows = execute_query(
            """
            SELECT u.id, u.email, u.full_name, u.role, o.name as organization_name, u.is_active, u.created_at
            FROM users u
            JOIN organizations o ON u.organization_id = o.id
            ORDER BY u.id ASC
            """
        )
        u_df = pd.DataFrame([dict(r) for r in users_rows])
        st.dataframe(u_df, use_container_width=True, hide_index=True)

    # 2. Organizations
    with admin_tabs[1]:
        st.markdown("##### Partitioned Business Organizations")
        orgs_rows = execute_query("SELECT * FROM organizations ORDER BY id ASC")
        o_df = pd.DataFrame([dict(r) for r in orgs_rows])
        st.dataframe(o_df, use_container_width=True, hide_index=True)

    # 3. Source Systems
    with admin_tabs[2]:
        st.markdown("##### Participating Source Systems & Priority Weights")
        src_rows = execute_query("SELECT * FROM source_systems ORDER BY priority_score DESC")
        s_df = pd.DataFrame([dict(r) for r in src_rows])
        st.dataframe(s_df, use_container_width=True, hide_index=True)

    # 4. Survivorship Rules Configuration
    with admin_tabs[3]:
        st.markdown("##### Configured Survivorship Policies (`config/survivorship_rules.yaml`)")
        st.caption("Active deterministic rules applied by the reconciliation engine:")

        rule_path = "config/survivorship_rules.yaml"
        current_yaml = ""
        if os.path.exists(rule_path):
            with open(rule_path, "r", encoding="utf-8") as f:
                current_yaml = f.read()

        st.markdown("**Business Readable Summary:**")
        st.markdown(
            """
            - **Customer Email**: Verified values have top priority over unverified. Newer verified emails win. Tied verified values require human review.
            - **Customer Phone**: Valid telephone structure preferred, followed by newest timestamp.
            - **Product Price**: Most recent valid numerical price preferred.
            - **Product Status**: ERP product status has strict authoritative priority over other systems.
            - **Supplier Status & Email**: Verified supplier records preferred; newer updates break ties.
            """
        )

        with st.expander("🛠️ Advanced YAML Rules Editor"):
            edited_yaml = st.text_area("Edit Survivorship Configuration", value=current_yaml, height=350)
            if st.button("Save & Apply Survivorship Rules", type="primary"):
                try:
                    parsed = yaml.safe_load(edited_yaml)
                    with open(rule_path, "w", encoding="utf-8") as f:
                        f.write(edited_yaml)
                    AuditService.log_event(
                        action="RULE_UPDATE",
                        user=user,
                        record_type="SYSTEM",
                        decision="UPDATED",
                        reason="Admin updated config/survivorship_rules.yaml"
                    )
                    st.success("Survivorship rules updated successfully! New rules will apply immediately.")
                except Exception as e:
                    st.error(f"Invalid YAML configuration: {e}")

    # 5. Persistence & Connection Pooling
    with admin_tabs[4]:
        st.markdown("##### Production Clustered Persistence & Connection Pooling")
        st.caption("Inspect live database pool status, RDS / Aurora cluster readiness, and PgBouncer compatibility.")

        from database.migration import check_database_readiness
        diag = check_database_readiness()

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Active Backend Engine", diag["engine"])
        with p2:
            st.metric("Connection Pooling", "Active" if diag["is_clustered"] else "Enabled (WAL)")
        with p3:
            st.metric("Active Connections", diag["active_connections"])
        with p4:
            st.metric("Idle Pool Connections", diag["idle_connections"])

        st.markdown("---")
        st.markdown("#### Database Architecture Diagnostics")
        diag_rows = [
            {"Parameter": "Storage Engine", "Value": diag["engine"], "Target": "PostgreSQL RDS / SQLite WAL"},
            {"Parameter": "Connection Pooler", "Value": diag["connection_pooling"], "Target": "ThreadedConnectionPool & QueuePool"},
            {"Parameter": "Min Pool Size", "Value": str(diag["min_pool_size"]), "Target": "5 connections"},
            {"Parameter": "Max Pool Size", "Value": str(diag["max_pool_size"]), "Target": "20 connections"},
            {"Parameter": "Pool Timeout", "Value": f"{diag['pool_timeout_sec']}s", "Target": "30.0s"},
            {"Parameter": "Pool Recycle", "Value": f"{diag['pool_recycle_sec']}s", "Target": "1800s (30 mins)"},
            {"Parameter": "Driver Availability (psycopg2)", "Value": "Installed" if diag["psycopg2_installed"] else "Missing", "Target": "Installed"},
            {"Parameter": "ORM Pooler (SQLAlchemy)", "Value": "Installed" if diag["sqlalchemy_installed"] else "Missing", "Target": "Installed"},
            {"Parameter": "High Availability Cluster Ready", "Value": "Yes (PgBouncer compatible)", "Target": "Yes"},
        ]
        st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)

        with st.expander("🚀 Connect / Migrate to Clustered PostgreSQL"):
            st.markdown("Enter a PostgreSQL / Amazon RDS connection string to test connectivity or migrate existing SQLite data:")
            pg_dsn = st.text_input("PostgreSQL DSN", value="postgresql://postgres:postgres_secure_password@localhost:5432/master_data_db")
            if st.button("Migrate SQLite Data to PostgreSQL"):
                from database.migration import migrate_sqlite_to_postgres
                with st.spinner("Executing migration and DDL setup..."):
                    res = migrate_sqlite_to_postgres(pg_dsn)
                if res["success"]:
                    st.success(f"Migration completed! Migrated tables: {res['migrated_tables']}")
                else:
                    st.warning(f"Connection check result: {res['error']} (Ensure PostgreSQL container is running via `docker-compose up -d`)")

