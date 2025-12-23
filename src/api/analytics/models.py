from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class SessionAnalytics(SQLModel):
    """User session analytics."""
    session_id: str
    page_count: int
    total_duration: int
    first_page: str
    last_page: str
    started_at: datetime
    ended_at: datetime


class ConversionFunnel(SQLModel):
    """Conversion funnel step data."""
    step: int
    page: str
    visitors: int
    conversion_rate: Optional[float] = 0.0


class RetentionCohort(SQLModel):
    """User retention cohort data."""
    cohort_date: datetime
    period: int
    users: int
    retention_rate: float


class PageMetrics(SQLModel):
    """Page performance metrics."""
    page: str
    views: int
    unique_visitors: int
    avg_duration: float
    bounce_rate: float
    top_referrers: list[dict]


class TrafficSource(SQLModel):
    """Traffic source analytics."""
    source: str
    visits: int
    percentage: float


class DeviceAnalytics(SQLModel):
    """Device and browser analytics."""
    device_type: str
    browser: str
    os: str
    visits: int
    percentage: float
