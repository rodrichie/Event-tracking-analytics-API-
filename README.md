# Analytics API - Event Tracking with Real-Time Dashboard

**Own your data pipeline!**

A comprehensive analytics API service built with Python, FastAPI, and TimescaleDB featuring:
- Event tracking and analytics
- JWT authentication
- Advanced analytics endpoints
- Real-time dashboard with WebSocket support

## Features

### Core Features
- **Event Tracking**: Track page visits, user actions, and custom events
- **Time-Series Storage**: Efficient storage using TimescaleDB with automatic partitioning
- **User Authentication**: JWT-based authentication with bcrypt password hashing
- **Real-Time Dashboard**: Live event monitoring via WebSocket

### Analytics Endpoints
- **Session Analytics**: Track user sessions, durations, and navigation paths
- **Conversion Funnels**: Analyze user journey through multiple pages
- **Retention Analysis**: Cohort-based user retention metrics
- **Page Metrics**: Detailed page performance (views, bounce rate, avg duration)
- **Traffic Sources**: Referrer and source attribution
- **Device Analytics**: Browser, OS, and device type breakdown

### Authentication
- User registration and login
- JWT token-based authentication
- Protected endpoints with role-based access
- Superuser capabilities

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start the services
docker compose up --watch

# Stop the services
docker compose down

# Stop and remove volumes
docker compose down -v
```

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

#### Events
- `POST /api/events/` - Create new event
- `GET /api/events/` - Get aggregated events (time bucketing)
- `GET /api/events/{id}` - Get specific event

#### Analytics
- `GET /api/analytics/sessions` - User session analytics
- `GET /api/analytics/funnel` - Conversion funnel analysis
- `GET /api/analytics/retention` - Retention cohort analysis
- `GET /api/analytics/pages` - Page performance metrics
- `GET /api/analytics/traffic-sources` - Traffic source breakdown
- `GET /api/analytics/devices` - Device and browser analytics

#### Real-Time
- `GET /api/realtime/` - Access real-time dashboard
- `WS /api/realtime/ws` - WebSocket endpoint for live updates
- `GET /api/realtime/stats` - Get current statistics

### Real-Time Dashboard

Access the live dashboard at: `http://localhost:8002/api/realtime/`

Features:
- Live event stream
- Real-time metrics (total events, active sessions, page views/min)
- Beautiful, responsive UI
- WebSocket-based updates

## Environment Variables

**Important: Never commit your .env files with real credentials!**

Copy the example file and fill in your values:

```bash
cp .env.example .env.compose
```

### Required Variables

```env
# Database Configuration
DATABASE_URL=postgresql+psycopg://time-user:time-pw@db_service:5432/timescaledb
DB_TIMEZONE=UTC

# Server Configuration
PORT=8002

# Security - JWT Authentication (REQUIRED)
# Generate a secure key with: openssl rand -hex 32
SECRET_KEY=your-generated-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Generate Secure SECRET_KEY

```bash
# On Linux/Mac/Git Bash
openssl rand -hex 32

# On PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

**Note:** The application will fail to start if `SECRET_KEY` is not properly set.

## API Documentation

The API provides interactive documentation via OpenAPI/Swagger with detailed endpoint descriptions, request/response schemas, and tag-based grouping across Events, Authentication, Analytics, and Real-time modules.

Once running, visit:
- **Swagger UI**: <http://localhost:8002/docs> -- Interactive API explorer with "Try it out" functionality
- **ReDoc**: <http://localhost:8002/redoc> -- Clean, readable API reference
- **OpenAPI JSON**: <http://localhost:8002/openapi.json> -- Machine-readable specification

## Example Usage

### 1. Register a User

```bash
curl -X POST http://localhost:8002/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst",
    "email": "analyst@example.com",
    "password": "secure123",
    "full_name": "Data Analyst"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst",
    "password": "secure123"
  }'
```

### 3. Track an Event

```bash
curl -X POST http://localhost:8002/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "page": "/pricing",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "referrer": "https://google.com",
    "session_id": "abc123",
    "duration": 45
  }'
```

### 4. Get Analytics

```bash
# Get conversion funnel
curl "http://localhost:8002/api/analytics/funnel?pages=/&pages=/pricing&pages=/signup"

# Get session analytics
curl "http://localhost:8002/api/analytics/sessions?hours=24"

# Get page metrics
curl "http://localhost:8002/api/analytics/pages?limit=10"
```

## Technology Stack

- **FastAPI** - Modern Python web framework
- **SQLModel** - SQL database ORM with Pydantic integration
- **TimescaleDB** - PostgreSQL extension for time-series data
- **PostgreSQL** - Relational database
- **Docker** - Containerization
- **WebSockets** - Real-time communication
- **JWT** - Authentication tokens
- **Bcrypt** - Password hashing

## Project Structure

```
analytics-api/
├── src/
│   ├── main.py                 # Application entry point
│   └── api/
│       ├── auth/              # Authentication module
│       │   ├── models.py      # User models
│       │   ├── routing.py     # Auth endpoints
│       │   ├── security.py    # JWT & password utils
│       │   └── dependencies.py # Auth middleware
│       ├── events/            # Event tracking
│       │   ├── models.py      # Event models
│       │   └── routing.py     # Event endpoints
│       ├── analytics/         # Advanced analytics
│       │   ├── models.py      # Analytics schemas
│       │   └── routing.py     # Analytics endpoints
│       ├── realtime/          # Real-time features
│       │   ├── manager.py     # WebSocket manager
│       │   └── routing.py     # Dashboard & WebSocket
│       └── db/                # Database config
│           ├── config.py      # DB settings
│           └── session.py     # Connection management
├── nbs/                       # Jupyter notebooks
├── boot/                      # Startup scripts
├── Dockerfile.web            # Docker configuration
├── compose.yaml              # Docker Compose setup
└── requirements.txt          # Python dependencies
```

## Development

### Manual Setup (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/analytics"
export SECRET_KEY="your-secret-key"

# Run the application
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 