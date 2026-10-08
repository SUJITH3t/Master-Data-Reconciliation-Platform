"""Reconciliation Workspace with Side-by-Side Comparison, Evidence, and Actions."""

import json
import streamlit as st
import pandas as pd
from typing import Any, Dict, List

from services.approval_service import ApprovalService
from services.record_service import RecordService
from services.auth_service import AuthService
from ui.components import render_page_header, render_empty_state, render_side_by_side_comparison
from ui.styles import render_badge


def render_reconciliation_page(user: Dict[str, Any]):
    render_page_header(
        title="Reconciliation Workspace",
        subtitle="Review differences between your business systems and resolve master-data conflicts.",
        badge_text="Active Governance"
    )

    # 1. Batch Reconciliation Bar
    col_batch1, col_batch2 = st.columns([3, 1])
    with col_batch1:
        st.markdown(
            """
            <div style="background: #F1F5F9; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.85rem; color: #475569;">
                💡 <b>Deterministic Engine Ready:</b> Reconciles records using configured survivorship rules without human bias.
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_batch2:
        if st.button("🚀 Run Batch Reconciliation", type="primary", use_container_width=True):
            with st.spinner("Processing source records across enterprise systems..."):
                summary = ApprovalService.run_reconciliation_batch(user)
                st.success(
                    f"Reconciliation completed — {summary['resolved_automatically']} automatically resolved, "
                    f"{summary['manual_review']} routed to human review, {summary['failed']} unresolved."
                )
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Filter Bar
    f_c1, f_c2, f_c3, f_c4 = st.columns([1.2, 1.2, 1.2, 2.4])
    with f_c1:
        status_opt = st.selectbox(
            "Status",
            ["All Statuses", "PENDING", "MANUAL_REVIEW", "APPROVED", "PUBLISHED", "REJECTED"],
            key="rec_filter_status"
        )
    with f_c2:
        type_opt = st.selectbox(
            "Record Type",
            ["All Types", "Customer", "Product", "Supplier"],
            key="rec_filter_type"
        )
    with f_c3:
        issue_opt = st.selectbox(
            "Issue Type",
            ["All Issues", "Conflict", "Missing", "Stale", "Verification Mismatch"],
            key="rec_filter_issue"
        )
    with f_c4:
        search_query = st.text_input("Search ID, Value, or Case Number", placeholder="e.g. CUST-001, new@example.com...", key="rec_search")

    # 3. Query Cases
    cases = ApprovalService.get_cases(
        user=user,
        status_filter=status_opt if status_opt != "All Statuses" else None,
        record_type_filter=type_opt if type_opt != "All Types" else None,
        issue_filter=issue_opt if issue_opt != "All Issues" else None,
        search_query=search_query
    )

    if not cases:
        render_empty_state("No reconciliation cases match your selected filters.", icon="✨")
        return

    st.markdown(f"**Found {len(cases)} case{'s' if len(cases) != 1 else ''} needing review:**")

    # Selected case state
    selected_case_id = st.session_state.get("selected_case_id", cases[0]["id"])

    # 4. Two-column Layout: Case List on Left, Case Detail & Evidence on Right
    left_col, right_col = st.columns([1.3, 2.2], gap="medium")

    with left_col:
        st.markdown("##### 📋 Reconciliation Cases")
        for c in cases:
            is_selected = (c["id"] == selected_case_id)
            bg_style = "background: #EFF6FF; border: 2px solid #3B82F6;" if is_selected else "background: #FFFFFF; border: 1px solid #E2E8F0;"
            
            st.markdown(
                f"""
                <div style="{bg_style} border-radius: 8px; padding: 0.85rem; margin-bottom: 0.6rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                        <span style="font-weight: 700; color: #1E293B; font-size: 0.95rem;">
                            {c['record_type'].upper()} &bull; {c['business_id']}
                        </span>
                        <span>{render_badge(c['status'])}</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #475569; margin-bottom: 0.4rem;">
                        Field: <b>{c['field_name']}</b> &bull; Issue: <span style="color: #EA580C; font-weight: 600;">{c['issue_type']}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B;">
                        Recommended: <code style="color: #1E40AF; font-size: 0.85rem;">{str(c['recommended_value'] or 'Manual Review')}</code>
                    </div>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.2rem;">
                        Source: <b>{c['winning_source'] or 'None'}</b> &bull; Confidence: <b>{c['confidence_score']}%</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button(f"🔍 Inspect {c['business_id']} ({c['field_name']})", key=f"sel_btn_{c['id']}", use_container_width=True):
                st.session_state["selected_case_id"] = c["id"]
                st.rerun()

    with right_col:
        curr_case = ApprovalService.get_case_by_id(selected_case_id, user)
        if not curr_case:
            st.info("Select a case from the list on the left to inspect evidence.")
            return

        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 0.6rem; margin-bottom: 0.8rem;">
                    <div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">
                            {curr_case['record_type']}: {curr_case['business_id']}
                        </div>
                        <div style="font-size: 0.85rem; color: #64748B;">
                            Case Number: <code>{curr_case['case_number']}</code> &bull; Organization: <b>{curr_case.get('organization_name')}</b>
                        </div>
                    </div>
                    <div>{render_badge(curr_case['status'])}</div>
                </div>
            """,
            unsafe_allow_html=True
        )

        # 5. Side-by-Side System Comparison Matrix
        st.markdown("##### 🔍 What the Systems Currently Say")
        evidence = curr_case.get("evidence", {})
        candidates = evidence.get("candidates", [])
        
        # If candidates not in evidence, fetch raw source records
        if not candidates:
            src_records = RecordService.get_source_records_for_entity(
                curr_case["record_type"], curr_case["business_id"], user
            )
            from engine.freshness import evaluate_freshness
            for sr in src_records:
                f_val = sr["field_values"].get(curr_case["field_name"])
                f_stat, f_lbl, f_age = evaluate_freshness(f_val, sr["source_timestamp"])
                candidates.append({
                    "source": sr["source_system"],
                    "value": f_val,
                    "verification_status": sr["verification_status"],
                    "freshness_label": f_lbl,
                    "timestamp": sr["source_timestamp"]
                })

        render_side_by_side_comparison(candidates, curr_case["field_name"])

        # 6. Prominent Recommendation Card
        st.markdown("<br>", unsafe_allow_html=True)
        conf_score = curr_case.get("confidence_score", 0.0)
        conf_color = "#10B981" if conf_score >= 90 else ("#F59E0B" if conf_score >= 70 else "#EF4444")
        conf_tier = "High" if conf_score >= 90 else ("Medium" if conf_score >= 70 else "Low")

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 2px solid #E2E8F0; border-left: 6px solid {conf_color}; border-radius: 8px; padding: 1.1rem; margin: 1rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #475569; text-transform: uppercase;">
                        🏆 Recommended Master Value for {curr_case['field_name'].upper()}
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 0.2rem 0.6rem; border-radius: 20px; font-weight: 700; color: {conf_color}; font-size: 0.85rem;">
                        Confidence: {conf_score}% ({conf_tier})
                    </div>
                </div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #1E293B; margin-bottom: 0.4rem;">
                    {curr_case['recommended_value'] or '⚠️ No single winner (Requires Human Review)'}
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.8rem;">
                    Recommended Source: <b>{curr_case['winning_source'] or 'Ambiguous'}</b> &bull; Previous Master Value: <code>{curr_case['previous_value'] or 'None'}</code>
                </div>
                <div style="background: #FFFFFF; border-left: 3px solid #3B82F6; padding: 0.65rem 0.85rem; border-radius: 4px; font-size: 0.88rem; color: #334155; line-height: 1.45;">
                    <b>Why this value?</b><br>
                    {curr_case['explanation'] or curr_case['reason'] or 'Survivorship rule decision.'}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 7. Action Buttons (RBAC Protected)
        st.markdown("##### ⚡ Decision Actions")
        act_col1, act_col2, act_col3, act_col4 = st.columns(4)

        with act_col1:
            if AuthService.check_permission(user, "can_approve") and curr_case["status"] in ("PENDING", "MANUAL_REVIEW"):
                if st.button("✅ Approve", key=f"btn_app_{curr_case['id']}", type="primary", use_container_width=True):
                    success, msg = ApprovalService.approve_case(curr_case["id"], user)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.button("✅ Approve", disabled=True, use_container_width=True, help="Not authorized or already resolved.")

        with act_col2:
            if AuthService.check_permission(user, "can_publish") and curr_case["status"] in ("APPROVED", "PENDING"):
                if st.button("📤 Publish", key=f"btn_pub_{curr_case['id']}", use_container_width=True):
                    success, msg = ApprovalService.publish_case(curr_case["id"], user)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.button("📤 Publish", disabled=True, use_container_width=True, help="Must be Approved first.")

        with act_col3:
            if AuthService.check_permission(user, "can_request_manual_review") and curr_case["status"] != "MANUAL_REVIEW":
                with st.popover("👤 Manual Review", use_container_width=True):
                    st.write("**Route to Human Specialist Review**")
                    mr_reason = st.text_input("Reason for escalation", placeholder="e.g. Needs legal vendor check...", key=f"mr_txt_{curr_case['id']}")
                    if st.button("Confirm Escalation", key=f"mr_btn_{curr_case['id']}", type="primary"):
                        if not mr_reason:
                            st.error("Please enter an escalation reason.")
                        else:
                            success, msg = ApprovalService.request_manual_review(curr_case["id"], user, mr_reason)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            else:
                st.button("👤 Manual Review", disabled=True, use_container_width=True)

        with act_col4:
            if AuthService.check_permission(user, "can_reject") and curr_case["status"] not in ("REJECTED", "PUBLISHED"):
                with st.popover("❌ Reject", use_container_width=True):
                    st.write("**Reject Recommendation**")
                    rej_reason = st.text_input("Mandatory business reason", placeholder="e.g. Known typo in e-commerce...", key=f"rej_txt_{curr_case['id']}")
                    if st.button("Confirm Rejection", key=f"rej_btn_{curr_case['id']}", type="secondary"):
                        if not rej_reason:
                            st.error("A clear reason is required to reject.")
                        else:
                            success, msg = ApprovalService.reject_case(curr_case["id"], user, rej_reason)
                            if success:
                                st.warning(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            else:
                st.button("❌ Reject", disabled=True, use_container_width=True)

        # 8. Evidence & Audit Lineage Expanders
        with st.expander("📁 Supporting Evidence & Candidate Scores"):
            scores = evidence.get("scores", {})
            if scores:
                st.write("**Rule Evaluation Scores per Source System:**")
                score_df = pd.DataFrame(list(scores.items()), columns=["Source System", "Rule Score"]).sort_values(by="Rule Score", ascending=False)
                st.dataframe(score_df, use_container_width=True, hide_index=True)
            else:
                st.caption("No dynamic scoring weights stored for this item.")

        if user.get("role") == "Admin":
            with st.expander("⚙️ Technical Details (Admin Only)"):
                st.write("**Rule Execution Trace & Raw Evidence JSON:**")
                st.json(curr_case.get("evidence", {}))
