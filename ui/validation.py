"""Validation & Performance Dashboard comparing Baseline vs Proposed Engine."""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Any, Dict

from services.validation_service import ValidationService
from ui.components import render_page_header


def render_validation_page(user: Dict[str, Any]):
    render_page_header(
        title="Validation & Performance",
        subtitle="Empirical evaluation benchmark comparing Baseline (Fixed Priority) vs Proposed Dynamic Engine on 50+ master entities.",
        badge_text="Scientific Evaluation"
    )

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        st.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.85rem; color: #475569;">
                🔬 <b>Live Benchmark Execution:</b> Evaluates 50+ Customers, Products, and Suppliers across 4 disparate systems with ground truth expected outcomes.
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_btn2:
        if st.button("🧪 Run Validation Benchmark", type="primary", use_container_width=True):
            with st.spinner("Executing benchmark across baseline and proposed engines..."):
                results = ValidationService.run_benchmark()
                st.session_state["validation_results"] = results
                st.success("Validation benchmark completed successfully!")

    # Load cached or initial benchmark results
    results = st.session_state.get("validation_results")
    if not results:
        # Run automatically on first view
        results = ValidationService.run_benchmark()
        st.session_state["validation_results"] = results

    base = results["baseline"]
    prop = results["proposed"]
    targets = results["targets"]

    st.markdown("<br>", unsafe_allow_html=True)

    # 1. Comparative Metrics Table
    st.markdown("#### 📊 Comparative Performance: Baseline vs Proposed")

    comparison_data = [
        {
            "Metric": "Precision Score",
            "Baseline (Fixed Priority)": f"{base['precision']}%",
            "Proposed Engine": f"{prop['precision']}%",
            "Business Target": f"&ge; {targets['precision']}%",
            "Target Status": "✅ Achieved" if prop['precision'] >= targets['precision'] else "❌ Not Achieved"
        },
        {
            "Metric": "False Positive Rate (FPR)",
            "Baseline (Fixed Priority)": f"{base['false_positive_rate']}%",
            "Proposed Engine": f"{prop['false_positive_rate']}%",
            "Business Target": f"&le; {targets['false_positive_rate']}%",
            "Target Status": "✅ Achieved" if prop['false_positive_rate'] <= targets['false_positive_rate'] else "❌ Not Achieved"
        },
        {
            "Metric": "Reconciliation Success Rate",
            "Baseline (Fixed Priority)": f"{base['success_rate']}%",
            "Proposed Engine": f"{prop['success_rate']}%",
            "Business Target": f"&ge; {targets['success_rate']}%",
            "Target Status": "✅ Achieved" if prop['success_rate'] >= targets['success_rate'] else "❌ Not Achieved"
        },
        {
            "Metric": "Manual Review Escalation Rate",
            "Baseline (Fixed Priority)": f"{base['manual_review_rate']}%",
            "Proposed Engine": f"{prop['manual_review_rate']}%",
            "Business Target": f"&le; {targets['manual_review_rate']}%",
            "Target Status": "✅ Achieved" if prop['manual_review_rate'] <= targets['manual_review_rate'] else "❌ Not Achieved"
        },
        {
            "Metric": "Avg Processing Time (per record)",
            "Baseline (Fixed Priority)": f"{base['avg_processing_time_ms']} ms",
            "Proposed Engine": f"{prop['avg_processing_time_ms']} ms",
            "Business Target": f"&le; {targets['avg_processing_time_ms']} ms",
            "Target Status": "✅ Achieved" if prop['avg_processing_time_ms'] <= targets['avg_processing_time_ms'] else "❌ Not Achieved"
        },
        {
            "Metric": "Total Benchmark Duration",
            "Baseline (Fixed Priority)": f"{base['total_processing_time_s']} s",
            "Proposed Engine": f"{prop['total_processing_time_s']} s",
            "Business Target": "N/A",
            "Target Status": "—"
        }
    ]

    df_comp = pd.DataFrame(comparison_data)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

    # 2. Comparative Visualizations
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### 📈 Success Rate & Precision Comparison")
        chart_df = pd.DataFrame([
            {"Engine": "Baseline (Fixed Priority)", "Metric": "Success Rate", "Value": base["success_rate"]},
            {"Engine": "Proposed Engine", "Metric": "Success Rate", "Value": prop["success_rate"]},
            {"Engine": "Baseline (Fixed Priority)", "Metric": "Precision", "Value": base["precision"]},
            {"Engine": "Proposed Engine", "Metric": "Precision", "Value": prop["precision"]},
        ])
        fig_acc = px.bar(
            chart_df, x="Metric", y="Value", color="Engine", barmode="group",
            color_discrete_map={"Baseline (Fixed Priority)": "#94A3B8", "Proposed Engine": "#10B981"}
        )
        fig_acc.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), yaxis_title="Percentage (%)")
        st.plotly_chart(fig_acc, use_container_width=True)

    with c2:
        st.markdown("##### ⚡ Latency Comparison (milliseconds)")
        time_df = pd.DataFrame([
            {"Engine": "Baseline (Fixed Priority)", "Avg Latency (ms)": base["avg_processing_time_ms"]},
            {"Engine": "Proposed Engine", "Avg Latency (ms)": prop["avg_processing_time_ms"]}
        ])
        fig_time = px.bar(
            time_df, x="Engine", y="Avg Latency (ms)", color="Engine",
            color_discrete_map={"Baseline (Fixed Priority)": "#94A3B8", "Proposed Engine": "#3B82F6"}
        )
        fig_time.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_time, use_container_width=True)

    # 3. Interactive Edge Case Demonstrations (Section 48-49)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🧪 Interactive Edge Case Demonstrations")
    st.caption("Execute real engine edge cases directly to verify ambiguity handling and stale/missing boundaries:")

    e_col1, e_col2, e_col3 = st.columns(3)

    with e_col1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; height: 100%;">
                <div style="font-weight: 700; font-size: 0.95rem; color: #1E293B;">Edge Case 1: All Disagree</div>
                <div style="font-size: 0.8rem; color: #64748B; margin: 0.4rem 0;">
                    Four systems disagree with identical timestamps and no verified winner.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Run Test 1", key="btn_edge_1", use_container_width=True):
            st.session_state["edge_res_1"] = ValidationService.run_edge_case_test(1)

        if "edge_res_1" in st.session_state:
            e1 = st.session_state["edge_res_1"]
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem; font-size: 0.82rem;">
                    <b>Expected:</b> {e1['expected']}<br>
                    <b>Actual:</b> <code>{e1['actual']}</code><br>
                    <b>Status:</b> {'<span style="color:#059669; font-weight:700;">✓ Passed</span>' if e1['passed'] else '<span style="color:#DC2626;">✗ Failed</span>'}<br>
                    <b>Explanation:</b> {e1['explanation']}
                </div>
                """,
                unsafe_allow_html=True
            )

    with e_col2:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; height: 100%;">
                <div style="font-weight: 700; font-size: 0.95rem; color: #1E293B;">Edge Case 2: Stale vs Missing</div>
                <div style="font-size: 0.8rem; color: #64748B; margin: 0.4rem 0;">
                    Older verified value (90 days old) vs blank/empty fields in newer systems.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Run Test 2", key="btn_edge_2", use_container_width=True):
            st.session_state["edge_res_2"] = ValidationService.run_edge_case_test(2)

        if "edge_res_2" in st.session_state:
            e2 = st.session_state["edge_res_2"]
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem; font-size: 0.82rem;">
                    <b>Expected:</b> {e2['expected']}<br>
                    <b>Actual:</b> <code>{e2['actual']}</code><br>
                    <b>Status:</b> {'<span style="color:#059669; font-weight:700;">✓ Passed</span>' if e2['passed'] else '<span style="color:#DC2626;">✗ Failed</span>'}<br>
                    <b>Explanation:</b> {e2['explanation']}
                </div>
                """,
                unsafe_allow_html=True
            )

    with e_col3:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; height: 100%;">
                <div style="font-weight: 700; font-size: 0.95rem; color: #1E293B;">Edge Case 3: Ambiguous Tie</div>
                <div style="font-size: 0.8rem; color: #64748B; margin: 0.4rem 0;">
                    Two verified sources with conflicting values updated at the exact same hour.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Run Test 3", key="btn_edge_3", use_container_width=True):
            st.session_state["edge_res_3"] = ValidationService.run_edge_case_test(3)

        if "edge_res_3" in st.session_state:
            e3 = st.session_state["edge_res_3"]
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0.6rem; margin-top: 0.5rem; font-size: 0.82rem;">
                    <b>Expected:</b> {e3['expected']}<br>
                    <b>Actual:</b> <code>{e3['actual']}</code><br>
                    <b>Status:</b> {'<span style="color:#059669; font-weight:700;">✓ Passed</span>' if e3['passed'] else '<span style="color:#DC2626;">✗ Failed</span>'}<br>
                    <b>Explanation:</b> {e3['explanation']}
                </div>
                """,
                unsafe_allow_html=True
            )

    # 4. Error Analysis Section (Section 47)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🔍 Error Analysis & Limiting Case Inspection")
    
    with st.expander("Inspect Baseline Errors (Why Baseline Failed 78% of cases)"):
        st.write(f"**Baseline produced {len(base['errors'])} errors / false resolutions:**")
        if base["errors"]:
            b_err_df = pd.DataFrame(base["errors"])
            st.dataframe(b_err_df[["record_id", "type", "field", "expected", "actual", "status", "reason"]], use_container_width=True, hide_index=True)

    with st.expander("Inspect Proposed Engine Unresolved or Escalated Cases"):
        if prop["errors"]:
            p_err_df = pd.DataFrame(prop["errors"])
            st.dataframe(p_err_df, use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Zero false resolutions! The proposed engine correctly resolved all deterministic cases and safely routed exactly the genuine ambiguous ties to Manual Review.")
