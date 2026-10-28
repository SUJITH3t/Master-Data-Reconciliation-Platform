"""
Probabilistic Entity Linkage & Real-Time Streaming Ingestion Workspace View.
Features Fellegi-Sunter typo-tolerant matching, Soundex blocking,
Debezium CDC streaming monitor, and live real-time feed simulation.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict

from engine.probabilistic_linkage import FellegiSunterModel, ProbabilisticLinkageEngine
from services.streaming_ingestion import streaming_engine


def render_linkage_page(user: Dict[str, Any]):
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h1 style="font-size: 1.85rem; font-weight: 800; color: #1E293B; margin-bottom: 0.2rem;">
                🧬 Probabilistic Linkage & Real-Time Streaming
            </h1>
            <p style="color: #64748B; font-size: 0.95rem; margin-top: 0;">
                Typo-tolerant entity matching via Fellegi-Sunter methodology and high-throughput Kafka / Debezium CDC ingestion.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_linkage, tab_streaming, tab_benchmark = st.tabs([
        "🔬 Fellegi-Sunter Linkage Sandbox",
        "⚡ Real-Time Streaming & CDC Monitor",
        "📈 Empirical Accuracy Benchmark"
    ])

    # =================================================================
    # TAB 1: Fellegi-Sunter Probabilistic Linkage Sandbox
    # =================================================================
    with tab_linkage:
        st.markdown("### Interactive Typo-Tolerant Record Matcher")
        st.caption("Test how the Fellegi-Sunter log-likelihood model resolves phonetic variations, transposed characters, and typos.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📥 Record A (e.g. ERP Feed)")
            name_a = st.text_input("Entity Name (A)", value="Jonathon Smith", key="name_a")
            email_a = st.text_input("Email Address (A)", value="jsmith@retail-enterprise.com", key="email_a")
            phone_a = st.text_input("Phone Number (A)", value="555-123-4567", key="phone_a")
            addr_a = st.text_input("Street Address (A)", value="100 Market Street Apt 4B", key="addr_a")

        with col2:
            st.markdown("##### 📥 Record B (e.g. POS / Shopify Feed)")
            name_b = st.text_input("Entity Name (B)", value="Johnathan Smyth", key="name_b")
            email_b = st.text_input("Email Address (B)", value="jsmith@retail-enterprise.co", key="email_b")
            phone_b = st.text_input("Phone Number (B)", value="555-123-4567", key="phone_b")
            addr_b = st.text_input("Street Address (B)", value="100 Market St #4B", key="addr_b")

        entity_type = st.selectbox("Entity Model Domain", ["Customer", "Product", "Supplier"], key="linkage_domain")

        if st.button("⚡ Evaluate Fellegi-Sunter Linkage", type="primary", use_container_width=True):
            rec_a = {"name": name_a, "email": email_a, "phone": phone_a, "address": addr_a}
            rec_b = {"name": name_b, "email": email_b, "phone": phone_b, "address": addr_b}

            res = FellegiSunterModel.evaluate_pair(rec_a, rec_b, entity_type)

            st.markdown("---")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("Fellegi-Sunter Weight (W)", f"{res['fellegi_sunter_weight']:.2f}")
            with kpi2:
                badge_color = "#10B981" if res["classification"] == "DEFINITE_MATCH" else (
                    "#F59E0B" if res["classification"] == "POSSIBLE_MATCH" else "#EF4444"
                )
                st.markdown(
                    f"""
                    <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 0.6rem; text-align: center;">
                        <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">CLASSIFICATION</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: {badge_color}; margin-top: 0.2rem;">
                            {res['classification']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with kpi3:
                st.metric("Avg Jaro-Winkler", f"{res['average_jaro_winkler']:.3f}")
            with kpi4:
                st.metric("Avg N-Gram Cosine", f"{res['average_cosine']:.3f}")

            st.markdown("#### Field-Level Similarity & Weight Breakdown")
            field_rows = []
            for f, d in res["field_details"].items():
                field_rows.append({
                    "Field": f,
                    "Record A Value": d.get("val_a", "-"),
                    "Record B Value": d.get("val_b", "-"),
                    "Jaro-Winkler Similarity": d.get("jaro_winkler", 0.0),
                    "N-Gram Cosine Similarity": d.get("cosine", 0.0),
                    "Fellegi-Sunter Weight Contribution": d.get("weight", 0.0),
                    "Status": "Agreement" if d.get("agreement") else "Disagreement"
                })
            st.dataframe(pd.DataFrame(field_rows), use_container_width=True)

    # =================================================================
    # TAB 2: Real-Time Streaming & Debezium CDC Monitor
    # =================================================================
    with tab_streaming:
        st.markdown("### Asynchronous Kafka & Debezium CDC Ingestion Monitor")
        st.caption("High-throughput streaming ingestion pipeline consuming real-time order, inventory, and customer change events.")

        stream_metrics = streaming_engine.get_stream_metrics()

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total Events Ingested", stream_metrics["total_ingested"])
        with m2:
            st.metric("Events Processed", stream_metrics["total_processed"])
        with m3:
            st.metric("Queue Depth", stream_metrics["queue_depth"])
        with m4:
            st.metric("Avg Ingestion Lag", f"{stream_metrics['avg_lag_ms']:.2f} ms")
        with m5:
            st.metric("Throughput", f"{stream_metrics['throughput_eps']} eps")

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            if st.button("🚀 Simulate Real-Time Debezium Feed (15 Events)", type="primary", use_container_width=True):
                with st.spinner("Streaming real-time events through asynchronous worker pool..."):
                    streaming_engine.simulate_realtime_stream(count=15)
                st.success("Successfully ingested 15 real-time CDC events!")
                st.rerun()

        with col_info:
            st.info("Worker pool operates daemon threads consuming JSON envelopes compliant with the standard Debezium connector specification.")

        st.markdown("#### Recent Streaming CDC Events")
        if stream_metrics["recent_events"]:
            st.dataframe(pd.DataFrame(stream_metrics["recent_events"]), use_container_width=True)
        else:
            st.markdown("*No streaming events recorded yet. Click 'Simulate Real-Time Debezium Feed' above to trigger events.*")

    # =================================================================
    # TAB 3: Empirical Accuracy Benchmark
    # =================================================================
    with tab_benchmark:
        st.markdown("### Fellegi-Sunter Typo-Tolerance Benchmark")
        st.caption("Verifiable empirical evaluation across phonetic name variations, address abbreviations, marginal ties, and complete non-matches.")

        bench_data = ProbabilisticLinkageEngine.run_probabilistic_benchmark()

        b1, b2, b3 = st.columns(3)
        with b1:
            st.metric("Benchmark Accuracy", f"{bench_data['accuracy_pct']}%")
        with b2:
            st.metric("Total Test Cases", bench_data["total_tests"])
        with b3:
            st.metric("Passed Tests", f"{bench_data['passed']} / {bench_data['total_tests']}")

        st.dataframe(pd.DataFrame(bench_data["benchmark_results"]), use_container_width=True)
