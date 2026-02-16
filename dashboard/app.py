"""
Event Tracking Analytics — Interactive Dashboard
Connects directly to TimescaleDB for rich analytics.
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(
    page_title="Event Analytics",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://time-user:time-pw@db_service:5432/timescaledb",
)
# Convert to psycopg2 format
PG_DSN = DB_URL.replace("postgresql+psycopg://", "postgresql://")

COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "green": "#10b981",
    "red": "#ef4444",
    "orange": "#f59e0b",
    "blue": "#3b82f6",
}

# ── DB helpers ──────────────────────────────────────────────────────

@st.cache_resource
def get_conn():
    return psycopg2.connect(PG_DSN)


def run_query(sql, params=None):
    conn = get_conn()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        return df
    except Exception:
        conn.reset()
        df = pd.read_sql_query(sql, conn, params=params)
        return df


# ── Custom CSS ──────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .metric-card h3 { font-size: 0.85em; opacity: 0.9; margin-bottom: 5px; }
    .metric-card .value { font-size: 2em; font-weight: bold; }
    div[data-testid="stSidebar"] { background: linear-gradient(180deg, #1e1e2e 0%, #2d2d44 100%); }
    div[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────

st.sidebar.title("Event Analytics")
st.sidebar.markdown("---")

tab = st.sidebar.radio(
    "View",
    ["Overview", "Pages", "Traffic Sources", "Sessions", "Devices", "Funnel"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Filters")

days = st.sidebar.selectbox("Time period", [7, 14, 30], index=2)
since = datetime.utcnow() - timedelta(days=days)

# ── Tab: Overview ───────────────────────────────────────────────────

if tab == "Overview":
    st.title("Platform Overview")
    st.caption(f"Last {days} days")

    kpi = run_query("""
        SELECT
            count(*) AS total_events,
            count(DISTINCT session_id) AS total_sessions,
            count(DISTINCT page) AS unique_pages,
            round(avg(duration)::numeric, 1) AS avg_duration,
            count(DISTINCT ip_address) AS unique_visitors
        FROM eventmodel
        WHERE time >= %s
    """, [since])

    if not kpi.empty:
        r = kpi.iloc[0]
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Events", f"{int(r['total_events']):,}")
        c2.metric("Sessions", f"{int(r['total_sessions']):,}")
        c3.metric("Unique Pages", int(r['unique_pages']))
        c4.metric("Avg Duration", f"{r['avg_duration']}s")
        c5.metric("Unique Visitors", f"{int(r['unique_visitors']):,}")

    st.markdown("---")

    # Daily events trend
    daily = run_query("""
        SELECT
            time_bucket('1 day', time) AS day,
            count(*) AS events,
            count(DISTINCT session_id) AS sessions
        FROM eventmodel
        WHERE time >= %s
        GROUP BY day ORDER BY day
    """, [since])

    if not daily.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily["day"], y=daily["events"],
            name="Events", mode="lines+markers",
            line=dict(color=COLORS["primary"], width=2),
        ))
        fig.add_trace(go.Scatter(
            x=daily["day"], y=daily["sessions"],
            name="Sessions", mode="lines+markers",
            yaxis="y2",
            line=dict(color=COLORS["green"], width=2),
        ))
        fig.update_layout(
            title="Daily Events & Sessions",
            yaxis_title="Events", yaxis2=dict(title="Sessions", overlaying="y", side="right"),
            hovermode="x unified", height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        hourly = run_query("""
            SELECT extract(hour FROM time)::int AS hour, count(*) AS events
            FROM eventmodel WHERE time >= %s
            GROUP BY hour ORDER BY hour
        """, [since])
        if not hourly.empty:
            fig_h = px.bar(hourly, x="hour", y="events", title="Events by Hour of Day",
                           color="events", color_continuous_scale="Purples")
            fig_h.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig_h, use_container_width=True)

    with col2:
        top_pages = run_query("""
            SELECT page, count(*) AS views
            FROM eventmodel WHERE time >= %s
            GROUP BY page ORDER BY views DESC LIMIT 10
        """, [since])
        if not top_pages.empty:
            fig_p = px.bar(top_pages, x="views", y="page", orientation="h",
                           title="Top 10 Pages", color="views",
                           color_continuous_scale="Blues")
            fig_p.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, height=350)
            st.plotly_chart(fig_p, use_container_width=True)

# ── Tab: Pages ──────────────────────────────────────────────────────

elif tab == "Pages":
    st.title("Page Performance")

    pages = run_query("""
        SELECT
            page,
            count(*) AS views,
            count(DISTINCT session_id) AS unique_visitors,
            round(avg(duration)::numeric, 1) AS avg_duration
        FROM eventmodel
        WHERE time >= %s
        GROUP BY page ORDER BY views DESC
    """, [since])

    if not pages.empty:
        st.dataframe(pages, use_container_width=True, hide_index=True)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.treemap(pages, path=["page"], values="views", title="Page Views Treemap",
                             color="avg_duration", color_continuous_scale="RdYlGn_r")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.scatter(pages, x="views", y="avg_duration", size="unique_visitors",
                              text="page", title="Views vs Duration",
                              color="unique_visitors", color_continuous_scale="Viridis")
            fig2.update_traces(textposition="top center")
            st.plotly_chart(fig2, use_container_width=True)

# ── Tab: Traffic Sources ────────────────────────────────────────────

elif tab == "Traffic Sources":
    st.title("Traffic Sources")

    sources = run_query("""
        SELECT
            CASE
                WHEN referrer IS NULL OR referrer = '' THEN 'Direct'
                WHEN referrer ILIKE '%%google%%' THEN 'Google'
                WHEN referrer ILIKE '%%facebook%%' THEN 'Facebook'
                WHEN referrer ILIKE '%%twitter%%' THEN 'Twitter'
                WHEN referrer ILIKE '%%linkedin%%' THEN 'LinkedIn'
                WHEN referrer ILIKE '%%reddit%%' THEN 'Reddit'
                WHEN referrer ILIKE '%%ycombinator%%' THEN 'Hacker News'
                WHEN referrer ILIKE '%%dev.to%%' THEN 'Dev.to'
                ELSE 'Other'
            END AS source,
            count(*) AS visits
        FROM eventmodel
        WHERE time >= %s
        GROUP BY source ORDER BY visits DESC
    """, [since])

    if not sources.empty:
        total = sources["visits"].sum()
        sources["pct"] = (sources["visits"] / total * 100).round(1)

        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(sources, values="visits", names="source",
                         title="Traffic Distribution", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(sources, use_container_width=True, hide_index=True)

        # Source over time
        source_daily = run_query("""
            SELECT
                time_bucket('1 day', time) AS day,
                CASE
                    WHEN referrer IS NULL OR referrer = '' THEN 'Direct'
                    WHEN referrer ILIKE '%%google%%' THEN 'Google'
                    WHEN referrer ILIKE '%%facebook%%' THEN 'Facebook'
                    WHEN referrer ILIKE '%%twitter%%' THEN 'Twitter'
                    WHEN referrer ILIKE '%%linkedin%%' THEN 'LinkedIn'
                    ELSE 'Other'
                END AS source,
                count(*) AS visits
            FROM eventmodel WHERE time >= %s
            GROUP BY day, source ORDER BY day
        """, [since])
        if not source_daily.empty:
            fig2 = px.area(source_daily, x="day", y="visits", color="source",
                           title="Traffic Sources Over Time")
            st.plotly_chart(fig2, use_container_width=True)

# ── Tab: Sessions ───────────────────────────────────────────────────

elif tab == "Sessions":
    st.title("Session Analytics")

    sessions = run_query("""
        SELECT
            session_id,
            count(*) AS page_count,
            sum(duration) AS total_duration,
            min(time) AS started_at,
            max(time) AS ended_at,
            min(page) AS first_page
        FROM eventmodel
        WHERE time >= %s AND session_id IS NOT NULL AND session_id != ''
        GROUP BY session_id
        ORDER BY started_at DESC
        LIMIT 200
    """, [since])

    if not sessions.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Sessions", f"{len(sessions):,}")
        col2.metric("Avg Pages/Session", f"{sessions['page_count'].mean():.1f}")
        col3.metric("Avg Session Duration", f"{sessions['total_duration'].mean():.0f}s")

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(sessions, x="page_count", nbins=20,
                               title="Pages per Session Distribution",
                               color_discrete_sequence=[COLORS["primary"]])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.histogram(sessions, x="total_duration", nbins=30,
                                title="Session Duration Distribution (seconds)",
                                color_discrete_sequence=[COLORS["green"]])
            st.plotly_chart(fig2, use_container_width=True)

        # Bounce rate
        bounce = run_query("""
            SELECT
                count(*) FILTER (WHERE pc = 1) AS bounces,
                count(*) AS total
            FROM (
                SELECT session_id, count(*) AS pc
                FROM eventmodel
                WHERE time >= %s AND session_id IS NOT NULL AND session_id != ''
                GROUP BY session_id
            ) s
        """, [since])
        if not bounce.empty:
            br = bounce.iloc[0]
            rate = br["bounces"] / br["total"] * 100 if br["total"] > 0 else 0
            st.metric("Bounce Rate", f"{rate:.1f}%")

        st.subheader("Recent Sessions")
        st.dataframe(sessions.head(50), use_container_width=True, hide_index=True)

# ── Tab: Devices ────────────────────────────────────────────────────

elif tab == "Devices":
    st.title("Device & Browser Analytics")

    devices = run_query("""
        SELECT
            CASE
                WHEN user_agent ILIKE '%%mobile%%' OR user_agent ILIKE '%%android%%'
                     OR user_agent ILIKE '%%iphone%%' THEN 'Mobile'
                WHEN user_agent ILIKE '%%ipad%%' OR user_agent ILIKE '%%tablet%%' THEN 'Tablet'
                ELSE 'Desktop'
            END AS device,
            CASE
                WHEN user_agent ILIKE '%%chrome%%' AND user_agent NOT ILIKE '%%edg%%' THEN 'Chrome'
                WHEN user_agent ILIKE '%%firefox%%' THEN 'Firefox'
                WHEN user_agent ILIKE '%%safari%%' AND user_agent NOT ILIKE '%%chrome%%' THEN 'Safari'
                WHEN user_agent ILIKE '%%edg%%' THEN 'Edge'
                ELSE 'Other'
            END AS browser,
            CASE
                WHEN user_agent ILIKE '%%windows%%' THEN 'Windows'
                WHEN user_agent ILIKE '%%macintosh%%' THEN 'macOS'
                WHEN user_agent ILIKE '%%iphone%%' OR user_agent ILIKE '%%ipad%%' THEN 'iOS'
                WHEN user_agent ILIKE '%%android%%' THEN 'Android'
                WHEN user_agent ILIKE '%%linux%%' THEN 'Linux'
                ELSE 'Other'
            END AS os,
            count(*) AS visits
        FROM eventmodel
        WHERE time >= %s
        GROUP BY device, browser, os
        ORDER BY visits DESC
    """, [since])

    if not devices.empty:
        col1, col2, col3 = st.columns(3)

        with col1:
            dev_agg = devices.groupby("device")["visits"].sum().reset_index()
            fig = px.pie(dev_agg, values="visits", names="device",
                         title="Device Type", hole=0.45,
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            br_agg = devices.groupby("browser")["visits"].sum().reset_index()
            fig2 = px.pie(br_agg, values="visits", names="browser",
                          title="Browser", hole=0.45,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, use_container_width=True)

        with col3:
            os_agg = devices.groupby("os")["visits"].sum().reset_index()
            fig3 = px.pie(os_agg, values="visits", names="os",
                          title="Operating System", hole=0.45,
                          color_discrete_sequence=px.colors.qualitative.Bold)
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Detailed Breakdown")
        st.dataframe(devices, use_container_width=True, hide_index=True)

# ── Tab: Funnel ─────────────────────────────────────────────────────

elif tab == "Funnel":
    st.title("Conversion Funnel")

    funnel_pages = ["/", "/pricing", "/signup", "/dashboard"]

    steps = []
    for i, page in enumerate(funnel_pages):
        row = run_query("""
            SELECT count(DISTINCT session_id) AS visitors
            FROM eventmodel
            WHERE page = %s AND time >= %s
              AND session_id IS NOT NULL AND session_id != ''
        """, [page, since])
        if not row.empty:
            visitors = int(row.iloc[0]["visitors"])
            steps.append({"step": i + 1, "page": page, "visitors": visitors})

    if steps:
        df = pd.DataFrame(steps)
        df["conversion"] = (df["visitors"] / df["visitors"].iloc[0] * 100).round(1)
        df["drop_off"] = (100 - df["conversion"]).round(1)

        fig = go.Figure(go.Funnel(
            y=df["page"],
            x=df["visitors"],
            textinfo="value+percent initial",
            marker=dict(color=[COLORS["blue"], COLORS["primary"],
                               COLORS["secondary"], COLORS["green"]]),
        ))
        fig.update_layout(title="Conversion Funnel", height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(df, use_container_width=True, hide_index=True)

        # Overall conversion rate
        if len(steps) >= 2:
            overall = steps[-1]["visitors"] / steps[0]["visitors"] * 100 if steps[0]["visitors"] > 0 else 0
            st.metric("Overall Conversion Rate", f"{overall:.1f}%")

# ── Footer ──────────────────────────────────────────────────────────

st.sidebar.markdown("---")
st.sidebar.markdown("**Event Analytics v1.0**")
st.sidebar.markdown(f"*{days}-day window*")
