import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select, func
from api.db.session import get_session
from api.events.models import EventModel
from .manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the real-time analytics dashboard."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-Time Analytics Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .status.connected {
            border-left: 5px solid #10b981;
        }
        
        .status.disconnected {
            border-left: 5px solid #ef4444;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
        }
        
        .metric-card h3 {
            color: #6b7280;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        
        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .events-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .events-section h2 {
            margin-bottom: 20px;
            color: #667eea;
        }
        
        .event-item {
            padding: 15px;
            border-left: 4px solid #667eea;
            background: #f9fafb;
            margin-bottom: 10px;
            border-radius: 5px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .event-time {
            color: #6b7280;
            font-size: 0.85em;
        }
        
        .event-page {
            font-weight: bold;
            color: #667eea;
            margin: 5px 0;
        }
        
        .event-details {
            font-size: 0.9em;
            color: #4b5563;
        }
        
        #eventsContainer {
            max-height: 500px;
            overflow-y: auto;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Real-Time Analytics Dashboard</h1>
        
        <div id="status" class="status disconnected">
            <strong>Status:</strong> <span id="statusText">Connecting...</span>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>Total Events</h3>
                <div class="metric-value" id="totalEvents">0</div>
            </div>
            <div class="metric-card">
                <h3>Active Sessions</h3>
                <div class="metric-value" id="activeSessions">0</div>
            </div>
            <div class="metric-card">
                <h3>Page Views/min</h3>
                <div class="metric-value" id="pageViewsPerMin">0</div>
            </div>
            <div class="metric-card">
                <h3>Avg Duration</h3>
                <div class="metric-value" id="avgDuration">0s</div>
            </div>
        </div>
        
        <div class="events-section">
            <h2>Live Events</h2>
            <div id="eventsContainer"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/api/realtime/ws`);
        const maxEvents = 50;
        let events = [];
        let metrics = {
            totalEvents: 0,
            activeSessions: new Set(),
            recentEvents: []
        };
        
        ws.onopen = function() {
            document.getElementById('status').className = 'status connected';
            document.getElementById('statusText').textContent = 'Connected';
            
            // Send ping every 30 seconds to keep connection alive
            setInterval(() => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send('ping');
                }
            }, 30000);
            
            // Poll for new events
            pollEvents();
            setInterval(pollEvents, 2000);  // Poll every 2 seconds
        };
        
        ws.onclose = function() {
            document.getElementById('status').className = 'status disconnected';
            document.getElementById('statusText').textContent = 'Disconnected';
        };
        
        ws.onmessage = function(event) {
            if (event.data === 'pong') return;
            
            try {
                const data = JSON.parse(event.data);
                handleNewEvent(data);
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        };
        
        async function pollEvents() {
            try {
                const response = await fetch('/api/events/');
                const data = await response.json();
                
                if (data && data.length > 0) {
                    updateMetrics(data);
                }
            } catch (e) {
                console.error('Error polling events:', e);
            }
        }
        
        function updateMetrics(data) {
            // Calculate metrics from data
            const now = new Date();
            const oneMinuteAgo = new Date(now - 60000);
            
            metrics.totalEvents = data.reduce((sum, bucket) => sum + bucket.count, 0);
            
            // Estimate active sessions and page views per minute
            const recentBucket = data[0];
            if (recentBucket) {
                metrics.activeSessions.add(recentBucket.page);
                
                const avgDuration = recentBucket.avg_duration || 0;
                document.getElementById('avgDuration').textContent = 
                    `${Math.round(avgDuration)}s`;
                
                document.getElementById('pageViewsPerMin').textContent = 
                    recentBucket.count || 0;
            }
            
            document.getElementById('totalEvents').textContent = metrics.totalEvents;
            document.getElementById('activeSessions').textContent = 
                metrics.activeSessions.size;
        }
        
        function handleNewEvent(event) {
            events.unshift(event);
            if (events.length > maxEvents) {
                events = events.slice(0, maxEvents);
            }
            
            updateEventsList();
        }
        
        function updateEventsList() {
            const container = document.getElementById('eventsContainer');
            container.innerHTML = events.map(event => `
                <div class="event-item">
                    <div class="event-time">${new Date(event.time).toLocaleString()}</div>
                    <div class="event-page">${event.page}</div>
                    <div class="event-details">
                        ${event.os || 'Unknown'} |
                        ${event.duration || 0}s |
                        ${event.referrer || 'Direct'}
                    </div>
                </div>
            `).join('');
        }
        
        // Simulate some initial data
        setTimeout(() => {
            metrics.totalEvents = 1234;
            metrics.activeSessions = new Set(['/', '/about', '/pricing']);
            document.getElementById('totalEvents').textContent = metrics.totalEvents;
            document.getElementById('activeSessions').textContent = metrics.activeSessions.size;
        }, 1000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@router.get("/stats")
async def get_realtime_stats(session: Session = Depends(get_session)):
    """Get real-time statistics for the dashboard."""
    # Get total events count
    total_events = session.exec(select(func.count(EventModel.id))).first()
    
    # Get unique sessions
    active_sessions = session.exec(
        select(func.count(func.distinct(EventModel.session_id)))
        .where(EventModel.session_id.isnot(None))
    ).first()
    
    # Get average duration
    avg_duration = session.exec(
        select(func.avg(EventModel.duration))
    ).first()
    
    return {
        "total_events": total_events or 0,
        "active_sessions": active_sessions or 0,
        "avg_duration": round(avg_duration or 0, 2)
    }


async def broadcast_event(event_data: dict):
    """Broadcast a new event to all connected WebSocket clients."""
    message = json.dumps(event_data)
    await manager.broadcast(message)
