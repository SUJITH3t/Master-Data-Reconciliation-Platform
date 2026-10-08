"""Change History and Entity Lineage Timeline."""

import streamlit as st
import pandas as pd
from typing import Any, Dict

from services.history_service import HistoryService
from ui.components import render_page_header, render_empty_state


def render_history_page(user: Dict[str, Any]):
    render_page_header(
        title="Change History & Lineage",
        subtitle="Immutable audit trail of master record updates, winning source systems, and business approvers.",
        badge_text="Traceable Governance"
    )

    c1, c2 = st.columns([1.5, 2.5])
    with c1:
        type_filter = st.selectbox("Filter Entity Type", ["All Types", "Customer", "Product", "Supplier"], key="hist_type")
    with c2:
        search_id = st.text_input("Filter by Business ID", placeholder="e.g. CUST-001...", key="hist_search")

    records = HistoryService.get_change_history(
        user=user,
        record_type=type_filter if type_filter != "All Types" else None,
        business_id=search_id,
        limit=100
    )

    if not records:
        render_empty_state("No change history entries match your current search.", icon="📜")
        return

    st.write(f"**Found {len(records)} historical update events:**")

    for r in records:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; margin-bottom: 0.8rem; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <div>
                        <span style="font-size: 1.05rem; font-weight: 700; color: #1E293B;">
                            {r['record_type']} {r['business_id']}
                        </span> &bull; 
                        <span style="color: #475569; font-weight: 600;">Field: {r['field_name']}</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B;">
                        🕒 {str(r['created_at'])[:19]}
                    </div>
                </div>
                <div style="margin: 0.4rem 0; font-size: 0.9rem;">
                    <span style="color: #64748B;">Previous:</span> <code style="text-decoration: line-through; color: #DC2626;">{r['previous_value'] or '[None]'}</code> 
                    &nbsp;&rarr;&nbsp; 
                    <span style="color: #059669; font-weight: 700;">New Master:</span> <code style="color: #059669; font-weight: 700;">{r['new_value']}</code>
                </div>
                <div style="font-size: 0.82rem; color: #475569; background: #F8FAFC; padding: 0.4rem 0.6rem; border-radius: 4px; border-left: 3px solid #3B82F6;">
                    <b>Reason:</b> {r['reason']}<br>
                    <span style="font-size: 0.75rem; color: #64748B;">
                        Approved by: <b>{r['user_email']}</b> &bull; Winning Source: <b>{r['winning_source']}</b> &bull; Case: <code>{r.get('case_number') or 'Direct'}</code>
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
