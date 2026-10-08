"""Approval Queue Page for Governance Reviews."""

import streamlit as st
import pandas as pd
from typing import Any, Dict

from services.approval_service import ApprovalService
from services.auth_service import AuthService
from ui.components import render_page_header, render_empty_state
from ui.styles import render_badge


def render_approvals_page(user: Dict[str, Any]):
    render_page_header(
        title="Approval Queue",
        subtitle="Review recommendations that are ready for a business decision.",
        badge_text="Decision Ready"
    )

    # Filter tab options
    tabs = st.tabs(["⏳ Pending Approval", "👤 Manual Review Required", "✅ Approved / Ready to Publish", "All Decisions"])

    status_map = {
        0: "PENDING",
        1: "MANUAL_REVIEW",
        2: "APPROVED",
        3: None
    }

    for idx, tab in enumerate(tabs):
        with tab:
            filter_st = status_map[idx]
            cases = ApprovalService.get_cases(user=user, status_filter=filter_st)
            
            if not cases:
                render_empty_state(f"No cases found in this queue state.", icon="✨")
                continue

            st.write(f"**Showing {len(cases)} items:**")

            for c in cases:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 1.05rem; font-weight: 700; color: #1E293B;">{c['record_type']} {c['business_id']}</span> &bull; 
                                    <span style="font-size: 0.9rem; color: #475569;">Field: <b>{c['field_name']}</b></span>
                                </div>
                                <div>{render_badge(c['status'])}</div>
                            </div>
                            <div style="margin: 0.5rem 0; font-size: 0.88rem; color: #334155;">
                                Issue: <span style="color: #EA580C; font-weight: 600;">{c['issue_type']}</span> &bull; 
                                Recommended: <code style="font-weight: 700; color: #1D4ED8;">{str(c['recommended_value'] or 'Manual Review')}</code> &bull; 
                                Winning Source: <b>{c['winning_source'] or 'None'}</b> &bull; 
                                Confidence: <b>{c['confidence_score']}%</b>
                            </div>
                            <div style="background: #F8FAFC; border-left: 3px solid #64748B; padding: 0.4rem 0.6rem; font-size: 0.82rem; color: #475569; margin-bottom: 0.6rem;">
                                {c['explanation'] or c['reason']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Action buttons
                    b_cols = st.columns([1, 1, 1, 1, 3])
                    
                    with b_cols[0]:
                        if AuthService.check_permission(user, "can_approve") and c["status"] in ("PENDING", "MANUAL_REVIEW"):
                            if st.button("Approve", key=f"app_q_{c['id']}", type="primary", use_container_width=True):
                                ok, msg = ApprovalService.approve_case(c["id"], user)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.button("Approve", disabled=True, key=f"app_dis_{c['id']}", use_container_width=True)

                    with b_cols[1]:
                        if AuthService.check_permission(user, "can_publish") and c["status"] in ("APPROVED", "PENDING"):
                            if st.button("Publish", key=f"pub_q_{c['id']}", use_container_width=True):
                                ok, msg = ApprovalService.publish_case(c["id"], user)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.button("Publish", disabled=True, key=f"pub_dis_{c['id']}", use_container_width=True)

                    with b_cols[2]:
                        if AuthService.check_permission(user, "can_request_manual_review") and c["status"] != "MANUAL_REVIEW":
                            with st.popover("Manual Review", use_container_width=True):
                                m_note = st.text_input("Reason", placeholder="Escalate...", key=f"m_note_{c['id']}")
                                if st.button("Confirm", key=f"m_btn_{c['id']}"):
                                    ok, msg = ApprovalService.request_manual_review(c["id"], user, m_note or "Sent to manual review")
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                        else:
                            st.button("Manual Review", disabled=True, key=f"mr_dis_{c['id']}", use_container_width=True)

                    with b_cols[3]:
                        if AuthService.check_permission(user, "can_reject") and c["status"] not in ("REJECTED", "PUBLISHED"):
                            with st.popover("Reject", use_container_width=True):
                                r_note = st.text_input("Mandatory Reason", placeholder="Why reject?", key=f"r_note_{c['id']}")
                                if st.button("Reject", key=f"r_btn_{c['id']}"):
                                    if not r_note:
                                        st.error("Reason required.")
                                    else:
                                        ok, msg = ApprovalService.reject_case(c["id"], user, r_note)
                                        if ok:
                                            st.warning(msg)
                                            st.rerun()
                        else:
                            st.button("Reject", disabled=True, key=f"rej_dis_{c['id']}", use_container_width=True)
