"""Master Data Reconciliation Platform - Main Streamlit Application Entrypoint."""

import os
import sys

# Ensure project root is in pythonpath
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from database.seed import seed_database
from database.database import init_db
from ui.styles import ENTERPRISE_CSS, render_badge
from ui.login import render_login_page
from ui.dashboard import render_dashboard_page
from ui.reconciliation import render_reconciliation_page
from ui.approvals import render_approvals_page
from ui.records import render_records_page
from ui.validation import render_validation_page
from ui.history import render_history_page
from ui.audit import render_audit_page
from ui.admin import render_admin_page
from ui.linkage import render_linkage_page
from ui.capacity import render_capacity_page

# Page Configuration
st.set_page_config(
    page_title="Master Data Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # 1. Automatic Database Initialization & Seeding on first boot
    if "db_initialized" not in st.session_state:
        seed_database(force=False)
        st.session_state["db_initialized"] = True

    # 2. Authentication Check
    user = st.session_state.get("user")
    if not user:
        render_login_page()
        return

    # Inject custom enterprise CSS for authenticated workspace
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)

    # 3. Sidebar Navigation & Role-Based Access Control
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.5rem 0; margin-bottom: 0.8rem; border-bottom: 1px solid #E2E8F0;">
                <div style="font-size: 1.35rem; font-weight: 800; color: #1E293B; letter-spacing: -0.02em;">
                    🛡️ MASTER DATA HUB
                </div>
                <div style="font-size: 0.76rem; color: #64748B; margin-top: 0.2rem; line-height: 1.3;">
                    Enterprise Data Reconciliation
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Active User Session Badge
        role_color = {
            "Admin": "#DC2626",
            "Reconciliation Specialist": "#2563EB",
            "Store Manager": "#D97706",
            "External Partner": "#7C3AED"
        }.get(user.get("role"), "#475569")

        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 1.2rem;">
                <div style="font-weight: 700; font-size: 0.88rem; color: #1E293B;">{user['full_name']}</div>
                <div style="font-size: 0.78rem; font-weight: 600; color: {role_color};">{user['role']}</div>
                <div style="font-size: 0.72rem; color: #64748B; margin-top: 0.15rem;">🏢 {user['organization_name']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Menu options filtered by Role Permissions
        menu_items = [
            ("🏠 Dashboard", "Dashboard"),
            ("🔍 Reconciliation", "Reconciliation"),
            ("✅ Approval Queue", "Approval Queue"),
            ("🧬 Linkage & Streaming", "Linkage & Streaming"),
            ("🕸️ Lineage & Capacity", "Lineage & Capacity"),
            ("📋 Records", "Records"),
            ("📊 Validation", "Validation"),
            ("🕒 History", "History"),
        ]

        if user.get("role") in ("Admin", "Reconciliation Specialist"):
            menu_items.append(("🛡️ Audit Log", "Audit Log"))

        if user.get("role") == "Admin":
            menu_items.append(("⚙️ Administration", "Administration"))

        menu_labels = [m[0] for m in menu_items]
        selected_label = st.radio("Navigation", menu_labels, label_visibility="collapsed")
        
        # Map back to internal page name
        page_name = next(m[1] for m in menu_items if m[0] == selected_label)

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["user"] = None
            st.session_state["selected_case_id"] = None
            st.rerun()

    # 4. Error-Guarded Page Router
    try:
        if page_name == "Dashboard":
            render_dashboard_page(user)
        elif page_name == "Reconciliation":
            render_reconciliation_page(user)
        elif page_name == "Approval Queue":
            render_approvals_page(user)
        elif page_name == "Linkage & Streaming":
            render_linkage_page(user)
        elif page_name == "Lineage & Capacity":
            render_capacity_page(user)
        elif page_name == "Records":
            render_records_page(user)
        elif page_name == "Validation":
            render_validation_page(user)
        elif page_name == "History":
            render_history_page(user)
        elif page_name == "Audit Log":
            render_audit_page(user)
        elif page_name == "Administration":
            render_admin_page(user)
    except Exception as e:
        st.markdown(
            f"""
            <div style="background: #FEF2F2; border: 1px solid #FECACA; border-radius: 8px; padding: 1.2rem; margin: 1rem 0;">
                <div style="color: #991B1B; font-weight: 700; font-size: 1.1rem;">⚠️ Something went wrong while processing this view.</div>
                <div style="color: #7F1D1D; font-size: 0.9rem; margin-top: 0.4rem;">
                    The system encountered an unexpected condition. Please retry or contact your system administrator.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if user.get("role") == "Admin":
            with st.expander("Administrative Diagnostic Trace"):
                st.exception(e)


if __name__ == "__main__":
    main()
