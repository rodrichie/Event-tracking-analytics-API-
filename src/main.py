from contextlib import asynccontextmanager
from typing import Union

from fastapi import FastAPI
from api.db.session import init_db
from api.events import router as event_router
from api.auth import router as auth_router
from api.analytics import router as analytics_router
from api.realtime import router as realtime_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before app startup
    init_db()
    yield
    # clean up


# OpenAPI tag metadata
tags_metadata = [
    {
        "name": "Events",
        "description": "Track and retrieve user interaction events. Supports time-bucketed queries with OS detection and page filtering. Events are stored in TimescaleDB hypertables for efficient time-series aggregation.",
    },
    {
        "name": "Authentication",
        "description": "User registration and JWT-based authentication. Supports role-based access control with superuser privileges for administrative endpoints.",
    },
    {
        "name": "Analytics",
        "description": (
            "Advanced analytics endpoints for platform insights:\n\n"
            "- **Session analytics** -- User sessions with page visits and durations\n"
            "- **Conversion funnels** -- Multi-step funnel analysis across pages\n"
            "- **Retention cohorts** -- Weekly user retention tracking\n"
            "- **Page metrics** -- Per-page performance with bounce rates and referrers\n"
            "- **Traffic sources** -- Referrer categorization (Direct, Google, Facebook, etc.)\n"
            "- **Device analytics** -- Device type, browser, and OS distribution\n"
        ),
    },
    {
        "name": "Real-time",
        "description": "WebSocket-powered real-time event streaming. Includes a live analytics dashboard with total events, active sessions, and event feed. Connect via WebSocket at `/api/realtime/ws` for push-based updates.",
    },
]

app = FastAPI(
    lifespan=lifespan,
    title="Event Tracking Analytics API",
    version="1.0.0",
    description=(
        "## Event Tracking and Analytics Platform\n\n"
        "A real-time event tracking and analytics API built on TimescaleDB "
        "for high-performance time-series data storage and analysis.\n\n"
        "### Features\n\n"
        "- **Event ingestion** -- Track page views, clicks, and custom events\n"
        "- **Time-series storage** -- TimescaleDB hypertables with automatic partitioning\n"
        "- **Session tracking** -- Automatic session detection and duration calculation\n"
        "- **Funnel analysis** -- Multi-step conversion funnel tracking\n"
        "- **Retention cohorts** -- Weekly cohort analysis for user retention\n"
        "- **Real-time dashboard** -- WebSocket-powered live event stream\n"
        "- **Device detection** -- Automatic OS, browser, and device type parsing\n\n"
        "### Data Architecture\n\n"
        "| Component | Technology |\n"
        "|---|---|\n"
        "| Time-series DB | TimescaleDB (PostgreSQL extension) |\n"
        "| Authentication | JWT with bcrypt password hashing |\n"
        "| Real-time | WebSocket connections |\n"
        "| API Framework | FastAPI with async support |\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    contact={
        "name": "Event Analytics Engineering",
        "url": "https://github.com/rodrichie/Event-tracking-analytics-API-",
    },
    license_info={
        "name": "MIT",
    },
)

app.include_router(event_router, prefix='/api/events', tags=['Events'])
app.include_router(auth_router, prefix='/api/auth', tags=['Authentication'])
app.include_router(analytics_router, prefix='/api/analytics', tags=['Analytics'])
app.include_router(realtime_router, prefix='/api/realtime', tags=['Real-time'])


@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "name": "Event Tracking Analytics API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "events": "/api/events",
            "auth": "/api/auth",
            "analytics": "/api/analytics",
            "realtime": "/api/realtime"
        }
    }


@app.get("/healthz")
def read_api_health():
    """Health check endpoint for container orchestration."""
    return {"status": "ok"}
