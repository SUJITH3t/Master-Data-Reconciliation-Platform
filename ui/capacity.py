"""
Lineage Explorer & Reviewer-Capacity Queuing Theory Simulator View.
Implements W3C PROV-O provenance visualization and Erlang-C staffing capacity modeling.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict

from services.lineage_service import LineageService
from services.capacity_analysis import CapacityAnalysisEngine
from database.database import execute_query


def render_capacity_page(user: Dict[str, Any]):
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; color: #1E293B; margin-bottom: 0.2rem;">
                🕸️ Lineage Provenance & Reviewer Capacity
            </h1>
            <p style="color: #64748B; font-size: 0.95rem; margin-top: 0;">
                W3C PROV-O master data provenance tracking and Erlang-C (M/M/c) queuing theory reviewer capacity sizing.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_prov, tab_queue, tab_matrix = st.tabs([
        "🌐 W3C PROV-O Lineage Explorer",
        "🧮 Erlang-C Capacity Simulator",
        "📊 Enterprise Scaling Matrix"
    ])

    # =================================================================
    # TAB 1: W3C PROV-O Lineage Explorer
    # =================================================================
    with tab_prov:
        st.markdown("### Master Data Provenance DAG Explorer")
        st.caption("Inspect the end-to-end W3C PROV-O lifecycle trace from source feeds through normalization, survivorship, and governance.")

        col1, col2 = st.columns([1, 2])
        with col1:
            rec_type = st.selectbox("Record Type", ["Customer", "Product", "Supplier"], key="prov_type")
            tbl = "customers" if rec_type == "Customer" else ("products" if rec_type == "Product" else "suppliers")
            rows = execute_query(f"SELECT business_id, name FROM {tbl} LIMIT 25")
            options = [f"{r['business_id']} - {r['name'] or 'Unnamed'}" for r in rows] if rows else ["CUST-001 - Demo"]
            selected_option = st.selectbox("Select Master Entity", options, key="prov_entity")
            biz_id = selected_option.split(" - ")[0].strip()

        with col2:
            st.markdown(
                """
                <div style="background: #F1F5F9; border-radius: 8px; padding: 0.8rem; font-size: 0.82rem; color: #475569;">
                    <b>W3C PROV-O Ontological Model:</b><br>
                    • <b>prov:Entity:</b> Raw Feed Payload &rarr; Normalized Record &rarr; Recommendation &rarr; Golden Master<br>
                    • <b>prov:Activity:</b> Ingestion &rarr; Normalization &rarr; Survivorship Resolution &rarr; Approval<br>
                    • <b>prov:Agent:</b> Operational Feeds (ERP/POS/Shopify) &rarr; Reviewer Stewards
                </div>
                """,
                unsafe_allow_html=True
            )

        provenance = LineageService.get_entity_provenance(rec_type, biz_id)

        st.markdown("---")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Entity ID", provenance["business_id"])
        with k2:
            st.metric("Contributing Sources", provenance["total_contributing_sources"])
        with k3:
            st.metric("Reconciliation Cases", provenance["reconciliation_cases_count"])
        with k4:
            st.metric("Audit Events", provenance["audit_events_count"])

        st.markdown("#### Provenance Lifecycle Graph (DAG)")
        nodes = provenance["graph"]["nodes"]
        edges = provenance["graph"]["edges"]

        node_df = pd.DataFrame([
            {
                "Node ID": n["id"],
                "Label": n["label"].replace("\n", " "),
                "PROV-O Class": n["prov_type"],
                "Platform Role": n["type"]
            }
            for n in nodes
        ])
        st.dataframe(node_df, use_container_width=True)

        if edges:
            st.markdown("#### Lineage Relationships")
            edge_df = pd.DataFrame([
                {
                    "Source Node": e["source"],
                    "Relationship": e["relation"],
                    "Target Node": e["target"]
                }
                for e in edges
            ])
            st.dataframe(edge_df, use_container_width=True)

    # =================================================================
    # TAB 2: Erlang-C Reviewer Capacity Simulator
    # =================================================================
    with tab_queue:
        st.markdown("### Erlang-C (M/M/c) Reviewer Capacity Simulator")
        st.caption("Model how manual review escalation rates, average handle times (AHT), and daily ingestion volumes impact required headcount and SLA compliance.")

        col_input1, col_input2 = st.columns(2)
        with col_input1:
            daily_vol = st.slider("Daily Master Updates Ingested", min_value=5000, max_value=250000, value=50000, step=5000)
            mr_rate_pct = st.slider("Manual Review Escalation Rate (%)", min_value=1.0, max_value=25.0, value=10.0, step=0.5)
            operating_hours = st.slider("Operating Hours Per Shift Day", min_value=6.0, max_value=24.0, value=8.0, step=1.0)

        with col_input2:
            aht_sec = st.slider("Average Handle Time (AHT) per Case (seconds)", min_value=30.0, max_value=300.0, value=120.0, step=10.0)
            target_sla_min = st.slider("Target SLA Queue Wait Time (minutes)", min_value=2.0, max_value=60.0, value=10.0, step=1.0)
            target_compliance = st.slider("Target SLA Compliance (%)", min_value=80.0, max_value=99.9, value=95.0, step=0.5)

        # Run Erlang-C evaluation
        cap_res = CapacityAnalysisEngine.evaluate_capacity(
            daily_ingestion_volume=daily_vol,
            manual_review_rate=mr_rate_pct / 100.0,
            operating_hours_per_day=operating_hours,
            average_handle_time_sec=aht_sec,
            target_sla_minutes=target_sla_min,
            target_sla_compliance_pct=target_compliance,
            shrinkage_pct=15.0
        )

        st.markdown("---")
        st.markdown("#### Capacity Sizing & Operational SLA Telemetry")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Daily Cases Needing Review", f"{cap_res['daily_review_cases']:,}")
        with c2:
            st.metric("Arrival Rate", f"{cap_res['arrival_rate_per_hour']} cases/hr")
        with c3:
            st.metric("Offered Load", f"{cap_res['offered_load_erlangs']} Erlangs")
        with c4:
            st.metric("Active Specialists (c)", cap_res["recommended_active_reviewers"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            st.metric("Required Gross FTE (15% Shrinkage)", f"{cap_res['required_gross_fte']} FTE")
        with c6:
            st.metric("Reviewer Utilization (ρ)", f"{cap_res['utilization_pct']}%")
        with c7:
            st.metric("Avg Queue Waiting Time", f"{cap_res['avg_queue_wait_minutes']} min")
        with c8:
            st.metric("SLA Compliance Rate", f"{cap_res['sla_compliance_pct']}%")

        # Fatigue warning
        burnout_color = "#10B981" if "Low" in cap_res["fatigue_risk_level"] else (
            "#F59E0B" if "Moderate" in cap_res["fatigue_risk_level"] else "#EF4444"
        )
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border-left: 4px solid {burnout_color}; padding: 0.8rem 1rem; border-radius: 4px; margin-top: 1rem;">
                <b>Specialist Workload:</b> {cap_res['cases_per_reviewer_hour']} cases per reviewer/hour. 
                <b>Fatigue Assessment:</b> <span style="color: {burnout_color}; font-weight: 700;">{cap_res['fatigue_risk_level']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =================================================================
    # TAB 3: Enterprise Scaling Matrix
    # =================================================================
    with tab_matrix:
        st.markdown("### Enterprise Workload Sizing Matrix")
        st.caption("Standard operational staffing benchmarks across retail scale tiers.")

        scaling_matrix = CapacityAnalysisEngine.generate_capacity_matrix()
        matrix_df = pd.DataFrame([
            {
                "Operating Tier": r["tier"],
                "Daily Ingest Volume": f"{r['daily_ingestion_volume']:,}",
                "Review Escalation": f"{r['manual_review_rate_pct']}%",
                "AHT (sec)": f"{r['average_handle_time_sec']}s",
                "Offered Load": f"{r['offered_load_erlangs']} Erlangs",
                "Active Specialists": r["recommended_active_reviewers"],
                "Gross FTE Headcount": r["required_gross_fte"],
                "Server Utilization": f"{r['utilization_pct']}%",
                "Avg Queue Delay": f"{r['avg_queue_wait_minutes']} min",
                "SLA Compliance": f"{r['sla_compliance_pct']}%"
            }
            for r in scaling_matrix
        ])
        st.dataframe(matrix_df, use_container_width=True)
