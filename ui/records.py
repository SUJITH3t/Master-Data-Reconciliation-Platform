"""Master Records Catalog and Inspection View."""

import streamlit as st
import pandas as pd
from typing import Any, Dict

from services.record_service import RecordService
from services.history_service import HistoryService
from ui.components import render_page_header, render_empty_state
from ui.styles import render_badge


def render_records_page(user: Dict[str, Any]):
    render_page_header(
        title="Master Records Catalog",
        subtitle="Browse and inspect trusted customer, product, and supplier master records across your organization.",
        badge_text="Golden Master"
    )

    search_term = st.text_input("🔍 Search Catalog by ID, Name, SKU, Email, or Phone", placeholder="Type to search...", key="rec_cat_search")

    tabs = st.tabs(["👤 Customers", "📦 Products", "🏭 Suppliers"])
    tab_entities = ["Customer", "Product", "Supplier"]

    for idx, ent_type in enumerate(tab_entities):
        with tabs[idx]:
            records = RecordService.get_master_records(
                entity_type=ent_type,
                user=user,
                search=search_term,
                limit=50
            )

            if not records:
                render_empty_state(f"No {ent_type} records found.", icon="📭")
                continue

            st.write(f"**Found {len(records)} {ent_type} records:**")

            # Convert to display table
            table_data = []
            for r in records:
                if ent_type == "Customer":
                    table_data.append({
                        "Business ID": r["business_id"],
                        "Name": r["name"],
                        "Email": r["email"],
                        "Phone": r["phone"],
                        "Organization": r.get("organization_name"),
                        "Data Quality": f"{r.get('data_quality_score', 100)}%",
                        "Status": r.get("status", "Active"),
                        "Last Reconciled": str(r.get("last_reconciled_at") or r.get("updated_at"))[:19]
                    })
                elif ent_type == "Product":
                    table_data.append({
                        "Business ID": r["business_id"],
                        "SKU": r["sku"],
                        "Product Name": r["name"],
                        "Price": f"${r['price']:,.2f}" if r.get("price") else "N/A",
                        "Category": r.get("category"),
                        "Status": r.get("status", "Active"),
                        "Organization": r.get("organization_name"),
                        "Last Reconciled": str(r.get("last_reconciled_at") or r.get("updated_at"))[:19]
                    })
                elif ent_type == "Supplier":
                    table_data.append({
                        "Business ID": r["business_id"],
                        "Supplier Name": r["name"],
                        "Email": r["email"],
                        "Phone": r["phone"],
                        "Verification": r.get("verification_status", "Unverified"),
                        "Status": r.get("status", "Active"),
                        "Organization": r.get("organization_name"),
                        "Last Reconciled": str(r.get("last_reconciled_at") or r.get("updated_at"))[:19]
                    })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Record Details Inspector
            st.markdown("---")
            st.markdown(f"##### 🔎 Inspect {ent_type} Lineage & Source Records")
            selected_id = st.selectbox(
                f"Select {ent_type} ID to inspect details:",
                [r["business_id"] for r in records],
                key=f"insp_sel_{ent_type}"
            )

            if selected_id:
                rec_detail = next((r for r in records if r["business_id"] == selected_id), None)
                if rec_detail:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.markdown("**Master Record Current Values:**")
                        st.json({k: v for k, v in rec_detail.items() if k not in ("id", "organization_id")})

                    with c2:
                        st.markdown("**Contributing Source Systems:**")
                        src_recs = RecordService.get_source_records_for_entity(ent_type, selected_id, user)
                        if src_recs:
                            for sr in src_recs:
                                st.markdown(f"- **{sr['source_system']}** (Timestamp: `{sr['source_timestamp']}` &bull; `{sr['verification_status']}`)")
                                with st.expander(f"Raw fields from {sr['source_system']}"):
                                    st.json(sr.get("field_values", {}))
                        else:
                            st.caption("No raw source records found.")

                    # Change History for this record
                    st.markdown("**Entity Change Timeline:**")
                    hist = HistoryService.get_change_history(user, record_type=ent_type, business_id=selected_id)
                    if hist:
                        for h in hist:
                            st.markdown(
                                f"""
                                <div style="background: #F8FAFC; border-left: 3px solid #3B82F6; padding: 0.5rem 0.8rem; border-radius: 4px; margin-bottom: 0.4rem; font-size: 0.85rem;">
                                    <b>{h['field_name']}</b>: <code>{h['previous_value']}</code> &rarr; <code style="color: #059669;">{h['new_value']}</code>
                                    <div style="font-size: 0.75rem; color: #64748B;">
                                        By {h['user_email']} &bull; Source: {h['winning_source']} &bull; {str(h['created_at'])[:19]}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        st.caption("No published changes recorded yet for this entity.")
