"""Professional Enterprise Website Login Screen with High-Contrast Typography."""

import streamlit as st
from services.auth_service import AuthService
from services.audit_service import AuditService
from ui.login_assets import LOGO_B64, DB_ILLUSTRATION_B64

LOGIN_CSS = """
<style>
/* Reset & Full Page Canvas */
.stApp {
    background: radial-gradient(circle at 10% 20%, rgba(37, 99, 235, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(59, 130, 246, 0.08) 0%, transparent 40%),
                #0b0f19 !important;
    color: #FFFFFF !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide Streamlit Header and Sidebar on Login */
header[data-testid="stHeader"] {
    display: none !important;
}

[data-testid="stSidebar"], section[data-testid="stSidebar"] {
    display: none !important;
}

/* Main Container Max Width */
.main .block-container {
    max-width: 1120px !important;
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
}

/* Brand Section Styling */
.brand-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(37, 99, 235, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    padding: 0.35rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #60A5FA;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

.brand-title-row {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 0.8rem;
}

.brand-logo {
    width: 48px;
    height: 48px;
    object-fit: contain;
    filter: drop-shadow(0 0 16px rgba(37, 99, 235, 0.5));
}

.brand-heading {
    font-size: 2.3rem;
    font-weight: 800;
    color: #FFFFFF !important;
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1.1;
}

.brand-tagline {
    font-size: 1.05rem;
    color: #CBD5E1 !important;
    line-height: 1.6;
    margin-bottom: 1.8rem;
    max-width: 460px;
}

.db-hero-wrapper {
    width: 100%;
    max-width: 420px;
    margin-top: 0.5rem;
    text-align: center;
}

.db-hero-img {
    width: 100%;
    height: auto;
    object-fit: contain;
    filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.6));
}

/* Feature badges */
.features-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 1.5rem;
}

.feature-pill {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.4rem 0.75rem;
    font-size: 0.82rem;
    color: #E2E8F0;
    font-weight: 500;
}

/* Website-Grade Elevated Card */
.auth-card {
    background: #162032 !important;
    border: 1px solid #2B3A4F !important;
    border-radius: 20px !important;
    padding: 2.6rem 2.2rem 2.2rem 2.2rem !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.05) !important;
    max-width: 460px;
    margin-left: auto;
    margin-right: auto;
}

.auth-card-title {
    font-size: 1.45rem;
    font-weight: 800;
    color: #FFFFFF !important;
    margin-bottom: 0.35rem;
    letter-spacing: -0.02em;
}

.auth-card-sub {
    font-size: 0.88rem;
    color: #94A3B8 !important;
    margin-bottom: 1.8rem;
}

/* Ultra High-Contrast Form Labels */
.field-label {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #F8FAFC !important;
    margin-bottom: 0.45rem !important;
    display: block !important;
    letter-spacing: -0.01em;
}

/* Streamlit Input Styling: High Visibility White Text & Crisp Borders */
div[data-testid="stTextInput"] {
    margin-bottom: 0.4rem !important;
}

div[data-testid="stTextInput"] label {
    display: none !important;
}

div[data-testid="stTextInput"] input {
    background-color: #0F172A !important;
    border: 1.5px solid #334155 !important;
    border-radius: 10px !important;
    color: #FFFFFF !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    padding: 0.75rem 1rem !important;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.2s ease !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #3B82F6 !important;
    background-color: #131E31 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #64748B !important;
    font-weight: 400 !important;
}

/* Vibrant Action Button */
button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    height: 48px !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4) !important;
    letter-spacing: -0.01em !important;
    transition: all 0.2s ease !important;
    margin-top: 0.5rem !important;
}

button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
    box-shadow: 0 6px 22px rgba(37, 99, 235, 0.55) !important;
    transform: translateY(-1px);
}

button[kind="primary"]:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3) !important;
}

/* Secondary Button (Demo Switcher) Styling */
button[kind="secondary"] {
    background-color: #1E293B !important;
    color: #E2E8F0 !important;
    border: 1px solid #334155 !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    border-radius: 8px !important;
    padding: 0.45rem 0.6rem !important;
    transition: all 0.15s ease !important;
}

button[kind="secondary"]:hover {
    background-color: #2D3D54 !important;
    border-color: #60A5FA !important;
    color: #FFFFFF !important;
}

/* Forgot Password / Footer Links */
.auth-footer-link {
    display: block;
    text-align: center;
    color: #60A5FA !important;
    font-size: 0.88rem;
    font-weight: 500;
    text-decoration: none;
    margin-top: 1.2rem;
    transition: color 0.15s ease;
}

.auth-footer-link:hover {
    color: #93C5FD !important;
    text-decoration: underline;
}

/* Demo Section */
.demo-divider {
    margin: 1.8rem 0 1rem 0;
    border-top: 1px solid #2B3A4F;
    position: relative;
    text-align: center;
}

.demo-divider-text {
    position: relative;
    top: -10px;
    background: #162032;
    padding: 0 12px;
    color: #94A3B8;
    font-size: 0.76rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

.stAlert {
    background-color: rgba(239, 68, 68, 0.18) !important;
    border: 1px solid #EF4444 !important;
    color: #FEE2E2 !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}
</style>
"""


def render_login_page():
    # Inject Custom High-Contrast SaaS CSS
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    col_brand, col_form = st.columns([1.15, 1.0], gap="large")

    # LEFT COLUMN: High-Contrast Brand Hero
    with col_brand:
        st.markdown(
            f"""
            <div style="padding-top: 0.5rem;">
                <div class="brand-badge">
                    <span>⚡ Enterprise Master Data Platform</span>
                </div>
                <div class="brand-title-row">
                    <img src="data:image/png;base64,{LOGO_B64}" class="brand-logo" alt="Master Data Hub Logo">
                    <h1 class="brand-heading">Master Data Hub</h1>
                </div>
                <p class="brand-tagline">
                    Reconcile and unify customer, product, and supplier records across your enterprise systems with automated survivorship and full audit governance.
                </p>
                <div class="db-hero-wrapper">
                    <img src="data:image/png;base64,{DB_ILLUSTRATION_B64}" class="db-hero-img" alt="Connected Retail Database Ecosystem">
                </div>
                <div class="features-grid">
                    <div class="feature-pill">🟢 Deterministic Survivorship</div>
                    <div class="feature-pill">🔍 Real-Time Conflict Detection</div>
                    <div class="feature-pill">🛡️ Immutable Audit Lineage</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # RIGHT COLUMN: High-Contrast Professional Login Card
    with col_form:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="auth-card-title">Sign In to Workspace</div>
            <div class="auth-card-sub">Access your authorized master records and reconciliation queues</div>
            """,
            unsafe_allow_html=True
        )

        with st.form("professional_login_form", border=False):
            st.markdown('<label class="field-label">Business Email Address</label>', unsafe_allow_html=True)
            email = st.text_input(
                "Business Email Address",
                value="",
                placeholder="name@company.com or user@retail.demo",
                key="input_email"
            )

            st.markdown('<label class="field-label" style="margin-top: 0.85rem;">Account Password</label>', unsafe_allow_html=True)
            password = st.text_input(
                "Account Password",
                value="",
                placeholder="Enter your password",
                type="password",
                key="input_password"
            )

            st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Sign In to Account", use_container_width=True, type="primary")

            if submit:
                if not email or not password:
                    st.error("Please enter both your business email and password.")
                else:
                    user = AuthService.authenticate(email, password)
                    if user:
                        st.session_state["user"] = user
                        AuditService.log_event("USER_LOGIN", user=user, decision="SUCCESS", reason="Standard business sign-in")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please check your email or password.")

        # Forgot Password Link
        st.markdown(
            '<a href="#" class="auth-footer-link" onclick="alert(\'For security in this evaluation build, use the demo profiles below.\'); return false;">Forgot your password?</a>',
            unsafe_allow_html=True
        )

        # Evaluator Demo Mode Section
        st.markdown(
            """
            <div class="demo-divider">
                <span class="demo-divider-text">Evaluator Demo Accounts</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        demo_c1, demo_c2 = st.columns(2)
        with demo_c1:
            if st.button("👑 Admin (Full Access)", key="btn_role_admin", use_container_width=True):
                user = AuthService.authenticate("admin@retail.demo", "Admin123!")
                if user:
                    st.session_state["user"] = user
                    AuditService.log_event("USER_LOGIN", user=user, decision="SUCCESS", reason="Demo sign-in: Admin")
                    st.rerun()

            if st.button("🏪 Store Manager", key="btn_role_mgr", use_container_width=True):
                user = AuthService.authenticate("manager@retail.demo", "Store123!")
                if user:
                    st.session_state["user"] = user
                    AuditService.log_event("USER_LOGIN", user=user, decision="SUCCESS", reason="Demo sign-in: Store Manager")
                    st.rerun()

        with demo_c2:
            if st.button("🔍 Recon Specialist", key="btn_role_spec", use_container_width=True):
                user = AuthService.authenticate("specialist@retail.demo", "Spec123!")
                if user:
                    st.session_state["user"] = user
                    AuditService.log_event("USER_LOGIN", user=user, decision="SUCCESS", reason="Demo sign-in: Specialist")
                    st.rerun()

            if st.button("🚚 Delivery Partner", key="btn_role_part", use_container_width=True):
                user = AuthService.authenticate("partner@delivery.demo", "Partner123!")
                if user:
                    st.session_state["user"] = user
                    AuditService.log_event("USER_LOGIN", user=user, decision="SUCCESS", reason="Demo sign-in: Partner")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
