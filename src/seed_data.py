"""
Seed realistic event data for the Event Tracking Analytics API.
Generates page visits, sessions, and user interactions over 30 days.
"""
import random
import time
import uuid
from datetime import datetime, timedelta
from decouple import config

import psycopg

DATABASE_URL = config("DATABASE_URL", default="")
# Convert SQLAlchemy URL to psycopg format
DB_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")

PAGES = [
    "/", "/about", "/pricing", "/contact",
    "/blog", "/products", "/login", "/signup",
    "/dashboard", "/settings", "/docs", "/faq",
    "/blog/getting-started", "/blog/analytics-tips",
    "/products/pro", "/products/enterprise",
]

REFERRERS = [
    None, "",
    "https://www.google.com/search",
    "https://www.google.com/search?q=analytics",
    "https://www.facebook.com/",
    "https://twitter.com/share",
    "https://www.linkedin.com/feed",
    "https://news.ycombinator.com",
    "https://www.reddit.com/r/webdev",
    "https://dev.to/analytics",
]

USER_AGENTS = [
    # Desktop Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Desktop Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Desktop Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    # Desktop Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Mobile Chrome
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
    # Mobile Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    # Tablet
    "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

# Session flow patterns (typical user journeys)
FLOWS = [
    ["/", "/pricing", "/signup"],
    ["/", "/about", "/contact"],
    ["/", "/products", "/products/pro", "/pricing", "/signup"],
    ["/", "/blog", "/blog/getting-started"],
    ["/", "/docs", "/faq"],
    ["/login", "/dashboard", "/settings"],
    ["/", "/products", "/products/enterprise", "/contact"],
    ["/blog/analytics-tips", "/pricing"],
    ["/"],  # Bounce
    ["/", "/about"],
]

DAYS = 30
EVENTS_PER_DAY_BASE = 150
IP_POOL_SIZE = 200


def wait_for_tables():
    """Wait for the app to create tables."""
    print("  Waiting for API to initialize tables...")
    for attempt in range(30):
        try:
            with psycopg.connect(DB_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT EXISTS (SELECT FROM information_schema.tables "
                        "WHERE table_name = 'eventmodel')"
                    )
                    if cur.fetchone()[0]:
                        print("  Tables ready.")
                        return True
        except Exception:
            pass
        time.sleep(2)
    print("  WARNING: Tables not found after 60s, attempting seed anyway.")
    return False


def check_already_seeded():
    """Check if data already exists."""
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM eventmodel")
                count = cur.fetchone()[0]
                if count > 0:
                    print(f"  Database already has {count} events — skipping seed.")
                    return True
    except Exception:
        pass
    return False


def generate_ip_pool(n):
    """Generate a pool of fake IPs."""
    return [f"192.168.{random.randint(1,254)}.{random.randint(1,254)}" for _ in range(n)]


def seed():
    print("=" * 50)
    print("  EVENT TRACKING — DATA SEEDER")
    print("=" * 50)

    wait_for_tables()

    if check_already_seeded():
        return

    ip_pool = generate_ip_pool(IP_POOL_SIZE)
    now = datetime.now()
    all_events = []

    for day_offset in range(DAYS, 0, -1):
        day = now - timedelta(days=day_offset)
        # Weekdays have more traffic
        dow = day.weekday()
        multiplier = 1.0 if dow < 5 else 0.6
        # Add growth trend
        trend = 0.7 + 0.3 * ((DAYS - day_offset) / DAYS)
        events_today = int(EVENTS_PER_DAY_BASE * multiplier * trend)

        for _ in range(events_today):
            # Pick a session flow
            flow = random.choice(FLOWS)
            session_id = str(uuid.uuid4())
            ip = random.choice(ip_pool)
            ua = random.choice(USER_AGENTS)
            referrer = random.choice(REFERRERS)

            # Time within the day (more traffic 9am-11pm)
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,3,5,8,10,10,9,8,8,9,10,10,9,8,7,6,5,3,2],
            )[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            event_time = day.replace(hour=hour, minute=minute, second=second)

            for page in flow:
                duration = random.randint(3, 300) if page != flow[-1] else random.randint(1, 60)
                all_events.append((
                    event_time, page, ua, ip,
                    referrer if page == flow[0] else "",
                    session_id, duration
                ))
                # Advance time within session
                event_time += timedelta(seconds=duration + random.randint(1, 5))

    # Shuffle to make it look natural
    random.shuffle(all_events)

    print(f"  Inserting {len(all_events)} events across {DAYS} days...")

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            batch_size = 200
            for i in range(0, len(all_events), batch_size):
                batch = all_events[i:i + batch_size]
                placeholders = []
                values = []
                for row in batch:
                    placeholders.append("(%s, %s, %s, %s, %s, %s, %s)")
                    values.extend(row)
                sql = (
                    "INSERT INTO eventmodel (time, page, user_agent, ip_address, "
                    "referrer, session_id, duration) VALUES " +
                    ",".join(placeholders)
                )
                cur.execute(sql, values)
            conn.commit()

    print(f"  Seeded {len(all_events)} events successfully.")
    print("=" * 50)


if __name__ == "__main__":
    seed()
