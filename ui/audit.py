"""Immutable Audit Log Viewer."""

import streamlit as st
import pandas as pd
from typing import Any, Dict

from services.audit_service import AuditService
from ui.components import render_page_header, render_empty_state


def render_audit_page(user: Dict[str, Any]):
    render_page_header(
        title="Enterprise Audit Log",
        subtitle="Cryptographically sealed, chronological audit trail recording all user, governance, and system events.",
        badge_text="Immutable Trail"
    )

    c1, c2, c3 = st.columns([1.5, 1.5, 2.5])
    with c1:
        action_filter = st.selectbox(
            "Action Filter",
            [
                "All Actions", "USER_LOGIN", "APPROVE_RECOMMENDATION", "REJECT_RECOMMENDATION",
                "REQUEST_MANUAL_REVIEW", "PUBLISH_MASTER_DATA", "RUN_BATCH_RECONCILIATION", "RULE_UPDATE"
            ],
            key="audit_act"
        )
    with c2:
        type_filter = st.selectbox("Record Type", ["All Types", "Customer", "Product", "Supplier", "SYSTEM"], key="audit_type")
    with c3:
        search_query = st.text_input("Search User, ID, or Reason", placeholder="Type to search audit logs...", key="audit_search")

    logs = AuditService.get_audit_logs(
        user=user,
        action_filter=action_filter,
        record_type_filter=type_filter,
        search_query=search_query,
        limit=100
    )

    if not logs:
        render_empty_state("No audit events match your selected filters.", icon="🛡️")
        return

    st.write(f"**Showing {len(logs)} audit entries:**")

    table_data = []
    for l in logs:
        table_data.append({
            "Timestamp": str(l["created_at"])[:19],
            "User Email": l["user_email"],
            "Role": l["role"],
            "Organization": l.get("organization_name", "Global"),
            "Action": l["action"],
            "Target": f"{l['record_type'] or ''} {l['business_id'] or ''}".strip() or "System",
            "Decision": l["decision"],
            "Reason": l["reason"],
            "IP Address": l["ip_address"]
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
