"""Reusable enterprise UI components."""

import streamlit as st
from typing import Any, Dict, List, Optional
from ui.styles import render_badge


def render_page_header(title: str, subtitle: str, badge_text: Optional[str] = None):
    """Render consistent modern page header."""
    col1, col2 = st.columns([3.5, 1])
    with col1:
        st.markdown(f'<div class="main-header-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="main-header-sub">{subtitle}</div>', unsafe_allow_html=True)
    with col2:
        if badge_text:
            st.markdown(f"<div style='text-align: right; margin-top: 10px;'>{render_badge(badge_text)}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 0.5rem 0 1.5rem 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)


def render_kpi(title: str, value: Any, subtitle: str = ""):
    """Render single KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_empty_state(message: str = "🎉 No records match your current criteria.", icon: str = "🔍"):
    """Render helpful business empty state."""
    st.markdown(
        f"""
        <div style="text-align: center; padding: 3.5rem 1.5rem; background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 12px; margin: 1.5rem 0;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: #334155;">{message}</div>
            <div style="font-size: 0.85rem; color: #64748B; margin-top: 0.3rem;">Try broadening your filters or selecting a different status.</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_side_by_side_comparison(candidates: List[Dict[str, Any]], field_name: str):
    """
    Renders side-by-side comparison table across source systems.
    Shows Value, Timestamp, Freshness Badge, Verification Badge.
    """
    if not candidates:
        st.info("No source records available for comparison.")
        return

    # Render as interactive horizontal columns
    cols = st.columns(len(candidates))
    for idx, c in enumerate(candidates):
        src = c.get("source", "System")
        val = c.get("value")
        val_display = str(val) if val is not None and str(val).strip() != "" else '<span style="color:#DC2626; font-style:italic;">[Missing]</span>'
        ver = c.get("verification_status", "Unverified")
        fresh_label = c.get("freshness_label", "Unknown")
        ts = str(c.get("timestamp", ""))[:19]

        ver_color = "#059669" if ver == "Verified" else "#64748B"

        with cols[idx]:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1rem; height: 100%;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: #1E293B; margin-bottom: 0.4rem; border-bottom: 2px solid #F1F5F9; padding-bottom: 0.3rem;">
                        {src}
                    </div>
                    <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.2rem;">Value:</div>
                    <div style="font-size: 1.05rem; font-weight: 600; color: #0F172A; word-break: break-all; margin-bottom: 0.5rem;">
                        {val_display}
                    </div>
                    <div style="font-size: 0.78rem; color: #64748B;">Freshness:</div>
                    <div style="margin-bottom: 0.4rem;">{render_badge(fresh_label)}</div>
                    <div style="font-size: 0.78rem; color: #64748B;">Verification:</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: {ver_color}; margin-bottom: 0.4rem;">
                        {'✓ ' + ver if ver == 'Verified' else '○ ' + ver}
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">Timestamp: {ts}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
