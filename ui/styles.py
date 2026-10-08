"""Enterprise CSS Styles, Color Tokens, and Card Components for Master Data Hub."""

ENTERPRISE_CSS = """
<style>
/* Modern Typography and Layout */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* App Header styling */
.main-header-title {
    font-size: 2.1rem;
    font-weight: 700;
    color: #1E293B;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}

.main-header-sub {
    font-size: 1.05rem;
    color: #64748B;
    margin-bottom: 1.5rem;
}

/* KPI Card styling */
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem 1.1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.kpi-title {
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #64748B;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.kpi-subtitle {
    font-size: 0.78rem;
    color: #94A3B8;
    margin-top: 0.35rem;
}

/* Status Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    line-height: 1;
}
.badge-fresh { background-color: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
.badge-stale { background-color: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
.badge-missing { background-color: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
.badge-conflict { background-color: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; }
.badge-approved { background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
.badge-published { background-color: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
.badge-manual { background-color: #FAF5FF; color: #6B21A8; border: 1px solid #E9D5FF; }
.badge-rejected { background-color: #FDF2F8; color: #9D174D; border: 1px solid #FBCFE8; }

/* Case Card in Workspace */
.recon-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    border-left: 5px solid #3B82F6;
}
.recon-card-conflict { border-left-color: #F97316; }
.recon-card-manual { border-left-color: #9333EA; }
.recon-card-published { border-left-color: #10B981; }

.recon-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1E293B;
}

/* User Session Badge */
.user-badge {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 1rem;
}
</style>
"""


def render_badge(status: str) -> str:
    """Render HTML badge pill."""
    status_lower = status.lower()
    if "fresh" in status_lower:
        cls = "badge-fresh"
        icon = "🟢"
    elif "stale" in status_lower:
        cls = "badge-stale"
        icon = "🟡"
    elif "missing" in status_lower:
        cls = "badge-missing"
        icon = "🔴"
    elif "conflict" in status_lower:
        cls = "badge-conflict"
        icon = "⚠️"
    elif "publish" in status_lower:
        cls = "badge-published"
        icon = "📤"
    elif "approv" in status_lower:
        cls = "badge-approved"
        icon = "✅"
    elif "manual" in status_lower:
        cls = "badge-manual"
        icon = "👤"
    elif "reject" in status_lower:
        cls = "badge-rejected"
        icon = "❌"
    else:
        cls = "badge-approved"
        icon = "ℹ️"
    return f'<span class="badge {cls}">{icon} {status}</span>'
