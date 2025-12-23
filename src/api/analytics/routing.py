from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func, case
from sqlalchemy import distinct, text
from timescaledb.hyperfunctions import time_bucket

from api.db.session import get_session
from api.events.models import EventModel
from .models import (
    SessionAnalytics, 
    ConversionFunnel, 
    RetentionCohort,
    PageMetrics,
    TrafficSource,
    DeviceAnalytics
)

router = APIRouter()


@router.get("/sessions", response_model=List[SessionAnalytics])
def get_session_analytics(
    hours: int = Query(default=24, description="Hours to look back"),
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session)
):
    """Get user session analytics with page visits and durations."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        select(
            EventModel.session_id,
            func.count(EventModel.id).label('page_count'),
            func.sum(EventModel.duration).label('total_duration'),
            func.min(EventModel.page).label('first_page'),
            func.max(EventModel.page).label('last_page'),
            func.min(EventModel.time).label('started_at'),
            func.max(EventModel.time).label('ended_at')
        )
        .where(
            EventModel.session_id.isnot(None),
            EventModel.session_id != "",
            EventModel.time >= since
        )
        .group_by(EventModel.session_id)
        .order_by(text('started_at DESC'))
        .limit(limit)
    )
    
    results = session.exec(query).fetchall()
    return results


@router.get("/funnel", response_model=List[ConversionFunnel])
def get_conversion_funnel(
    pages: List[str] = Query(
        default=["/", "/pricing", "/signup", "/dashboard"],
        description="Pages in funnel order"
    ),
    hours: int = Query(default=24),
    session: Session = Depends(get_session)
):
    """Analyze conversion funnel across specified pages."""
    since = datetime.utcnow() - timedelta(hours=hours)
    funnel_data = []
    
    total_visitors = session.exec(
        select(func.count(distinct(EventModel.session_id)))
        .where(EventModel.time >= since)
    ).first()
    
    for step, page in enumerate(pages, 1):
        visitors = session.exec(
            select(func.count(distinct(EventModel.session_id)))
            .where(
                EventModel.page == page,
                EventModel.time >= since
            )
        ).first()
        
        conversion_rate = (visitors / total_visitors * 100) if total_visitors > 0 else 0
        
        funnel_data.append({
            "step": step,
            "page": page,
            "visitors": visitors,
            "conversion_rate": round(conversion_rate, 2)
        })
    
    return funnel_data


@router.get("/retention", response_model=List[RetentionCohort])
def get_retention_analysis(
    days: int = Query(default=30, description="Days for cohort analysis"),
    session: Session = Depends(get_session)
):
    """Calculate user retention cohorts."""
    cohorts = []
    start_date = datetime.utcnow() - timedelta(days=days)
    
    for period in range(0, days, 7):  # Weekly cohorts
        cohort_start = start_date + timedelta(days=period)
        cohort_end = cohort_start + timedelta(days=7)
        
        # Users in cohort
        cohort_users = session.exec(
            select(func.count(distinct(EventModel.session_id)))
            .where(
                EventModel.time >= cohort_start,
                EventModel.time < cohort_end
            )
        ).first()
        
        # Retained users (visited again after cohort period)
        retained_users = session.exec(
            select(func.count(distinct(EventModel.session_id)))
            .where(
                EventModel.session_id.in_(
                    select(distinct(EventModel.session_id))
                    .where(
                        EventModel.time >= cohort_start,
                        EventModel.time < cohort_end
                    )
                ),
                EventModel.time >= cohort_end
            )
        ).first()
        
        retention_rate = (retained_users / cohort_users * 100) if cohort_users > 0 else 0
        
        cohorts.append({
            "cohort_date": cohort_start,
            "period": period // 7,
            "users": cohort_users,
            "retention_rate": round(retention_rate, 2)
        })
    
    return cohorts


@router.get("/pages", response_model=List[PageMetrics])
def get_page_metrics(
    hours: int = Query(default=24),
    limit: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """Get detailed metrics for each page."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = (
        select(
            EventModel.page,
            func.count(EventModel.id).label('views'),
            func.count(distinct(EventModel.session_id)).label('unique_visitors'),
            func.avg(EventModel.duration).label('avg_duration'),
        )
        .where(EventModel.time >= since)
        .group_by(EventModel.page)
        .order_by(text('views DESC'))
        .limit(limit)
    )
    
    results = session.exec(query).fetchall()
    
    # Calculate bounce rate (sessions with only 1 page view)
    metrics = []
    for row in results:
        single_page_sessions = session.exec(
            select(func.count(distinct(EventModel.session_id)))
            .where(
                EventModel.page == row.page,
                EventModel.session_id.in_(
                    select(EventModel.session_id)
                    .where(EventModel.time >= since)
                    .group_by(EventModel.session_id)
                    .having(func.count(EventModel.id) == 1)
                )
            )
        ).first()
        
        bounce_rate = (single_page_sessions / row.unique_visitors * 100) if row.unique_visitors > 0 else 0
        
        # Top referrers
        top_refs = session.exec(
            select(EventModel.referrer, func.count(EventModel.id).label('count'))
            .where(
                EventModel.page == row.page,
                EventModel.referrer.isnot(None),
                EventModel.referrer != "",
                EventModel.time >= since
            )
            .group_by(EventModel.referrer)
            .order_by(text('count DESC'))
            .limit(3)
        ).fetchall()
        
        metrics.append({
            "page": row.page,
            "views": row.views,
            "unique_visitors": row.unique_visitors,
            "avg_duration": round(row.avg_duration or 0, 2),
            "bounce_rate": round(bounce_rate, 2),
            "top_referrers": [{"referrer": r[0], "count": r[1]} for r in top_refs]
        })
    
    return metrics


@router.get("/traffic-sources", response_model=List[TrafficSource])
def get_traffic_sources(
    hours: int = Query(default=24),
    session: Session = Depends(get_session)
):
    """Analyze traffic sources and referrers."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    total_visits = session.exec(
        select(func.count(EventModel.id))
        .where(EventModel.time >= since)
    ).first()
    
    query = (
        select(
            case(
                (EventModel.referrer.is_(None), 'Direct'),
                (EventModel.referrer == '', 'Direct'),
                (EventModel.referrer.like('%google%'), 'Google'),
                (EventModel.referrer.like('%facebook%'), 'Facebook'),
                (EventModel.referrer.like('%twitter%'), 'Twitter'),
                (EventModel.referrer.like('%linkedin%'), 'LinkedIn'),
                else_='Other'
            ).label('source'),
            func.count(EventModel.id).label('visits')
        )
        .where(EventModel.time >= since)
        .group_by(text('source'))
        .order_by(text('visits DESC'))
    )
    
    results = session.exec(query).fetchall()
    
    sources = []
    for row in results:
        percentage = (row.visits / total_visits * 100) if total_visits > 0 else 0
        sources.append({
            "source": row.source,
            "visits": row.visits,
            "percentage": round(percentage, 2)
        })
    
    return sources


@router.get("/devices", response_model=List[DeviceAnalytics])
def get_device_analytics(
    hours: int = Query(default=24),
    session: Session = Depends(get_session)
):
    """Analyze device, browser, and OS usage."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    total_visits = session.exec(
        select(func.count(EventModel.id))
        .where(EventModel.time >= since)
    ).first()
    
    # Detect device type
    device_case = case(
        (EventModel.user_agent.ilike('%mobile%'), 'Mobile'),
        (EventModel.user_agent.ilike('%tablet%'), 'Tablet'),
        else_='Desktop'
    ).label('device_type')
    
    # Detect browser
    browser_case = case(
        (EventModel.user_agent.ilike('%chrome%'), 'Chrome'),
        (EventModel.user_agent.ilike('%firefox%'), 'Firefox'),
        (EventModel.user_agent.ilike('%safari%'), 'Safari'),
        (EventModel.user_agent.ilike('%edge%'), 'Edge'),
        else_='Other'
    ).label('browser')
    
    # Detect OS
    os_case = case(
        (EventModel.user_agent.ilike('%windows%'), 'Windows'),
        (EventModel.user_agent.ilike('%macintosh%'), 'MacOS'),
        (EventModel.user_agent.ilike('%iphone%'), 'iOS'),
        (EventModel.user_agent.ilike('%android%'), 'Android'),
        (EventModel.user_agent.ilike('%linux%'), 'Linux'),
        else_='Other'
    ).label('os')
    
    query = (
        select(
            device_case,
            browser_case,
            os_case,
            func.count(EventModel.id).label('visits')
        )
        .where(EventModel.time >= since)
        .group_by(device_case, browser_case, os_case)
        .order_by(text('visits DESC'))
    )
    
    results = session.exec(query).fetchall()
    
    analytics = []
    for row in results:
        percentage = (row.visits / total_visits * 100) if total_visits > 0 else 0
        analytics.append({
            "device_type": row.device_type,
            "browser": row.browser,
            "os": row.os,
            "visits": row.visits,
            "percentage": round(percentage, 2)
        })
    
    return analytics
