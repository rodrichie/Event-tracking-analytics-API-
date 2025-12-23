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
    # before app startup up
    init_db()
    yield
    # clean up


app = FastAPI(
    lifespan=lifespan, 
    title="Analytics API", 
    version="1.0.0",
    description="Event tracking analytics API with real-time dashboard"
)
app.include_router(event_router, prefix='/api/events', tags=['Events'])
app.include_router(auth_router, prefix='/api/auth', tags=['Authentication'])
app.include_router(analytics_router, prefix='/api/analytics', tags=['Analytics'])
app.include_router(realtime_router, prefix='/api/realtime', tags=['Real-time'])
# /api/events
# /api/auth
# /api/analytics
# /api/realtime


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/healthz")
def read_api_health():
    return {"status": "ok"}