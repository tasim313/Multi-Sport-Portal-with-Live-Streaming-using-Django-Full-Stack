# Multi-Sport Portal with Live Streaming

A production-ready, full-stack sports web application supporting **Cricket, Football, and Tennis** with live streaming, real-time score updates via WebSockets, a CMS, ad management, and role-based access control.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Architecture Diagram](#architecture-diagram)
5. [Getting Started (Local Development)](#getting-started-local-development)
6. [Environment Variables](#environment-variables)
7. [Running with Docker](#running-with-docker)
8. [API Reference](#api-reference)
9. [WebSocket Events](#websocket-events)
10. [User Roles & Permissions](#user-roles--permissions)
11. [Admin Panels](#admin-panels)
12. [Frontend Pages](#frontend-pages)
13. [Real-Time Score Updates Flow](#real-time-score-updates-flow)
14. [Celery Background Tasks](#celery-background-tasks)
15. [Deployment Checklist](#deployment-checklist)

---

## Project Overview

This portal allows users to:
- Watch **live sports streams** (YouTube, Vimeo, CDN, custom ISP links)
- See **real-time scores** updated via WebSocket without page refresh
- Read **news articles** managed via Wagtail CMS
- **Register/login** and manage their profile and favourite teams
- View **upcoming and finished matches** filtered by sport or league

Admins and editors can:
- Create and manage matches, stream sources, and score events
- Publish articles through the Wagtail CMS
- Configure ad placements with rotation and frequency capping
- Monitor all admin actions via a full audit log

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 5 + Django REST Framework |
| Database | PostgreSQL 15 |
| Real-time | Django Channels 4 + Redis (WebSockets) |
| ASGI Server | Daphne |
| CMS | Wagtail 5 |
| Task Queue | Celery + Celery Beat |
| Message Broker | Redis 7 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Frontend | React 18 + React Query + Tailwind CSS |
| Build Tool | Vite 5 |
| API Docs | drf-spectacular (Swagger UI / OpenAPI 3) |
| Security | django-csp, django-axes, HSTS, secure cookies |
| Deployment | Docker + docker-compose + Nginx |

---

## Project Structure

```
.
├── sports_portal/              # Django project package
│   ├── settings.py             # All settings (DB, Redis, JWT, CSP, etc.)
│   ├── urls.py                 # Root URL configuration
│   ├── asgi.py                 # ASGI + WebSocket routing
│   ├── celery.py               # Celery app definition
│   └── wsgi.py                 # WSGI fallback
│
├── sports/                     # Main Django app
│   ├── models.py               # All database models
│   ├── views.py                # API ViewSets + function-based views + serializers
│   ├── consumers.py            # WebSocket consumer (real-time scores)
│   ├── admin.py                # Django admin configuration
│   ├── tasks.py                # Celery background tasks
│   └── migrations/             # Database migrations
│
├── cms_content/                # Wagtail CMS app
│   ├── models.py               # Wagtail page models (HomePage, SportPage, etc.)
│   └── migrations/
│
├── App.jsx                     # React frontend (single file, all pages/components)
├── src/
│   ├── main.jsx                # React entry point
│   └── index.css               # Tailwind base styles
│
├── vite.config.js              # Vite config (proxy /api + /ws to Django)
├── tailwind.config.js          # Tailwind custom theme
├── postcss.config.js           # PostCSS config
├── package.json                # Node dependencies
│
├── load_sample_data.py         # Script to seed database with sample data
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker image for Django/Daphne
├── docker-compose.yml          # Multi-service Docker setup
├── entrypoint.sh               # Docker entrypoint (wait for DB + migrate)
└── nginx.conf                  # Nginx config (reverse proxy + WebSocket + static)
```

---

## Architecture Diagram

```
                  ┌──────────────────────────────────┐
                  │         Browser (React)           │
                  │     http://localhost:5173         │
                  └──────────────┬───────────────────┘
                                 │ HTTP + WebSocket
                                 ▼
                  ┌──────────────────────────────────┐
                  │         Nginx (port 80)           │
                  │  - Reverse proxy to Django        │
                  │  - Serve /static/ and /media/     │
                  │  - WebSocket upgrade headers      │
                  └──────────────┬───────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────┐
                  │    Daphne ASGI (port 8000)        │
                  │    Django 5 + Channels 4          │
                  ├───────────────┬──────────────────┤
                  │  REST API     │  WebSocket        │
                  │  /api/*       │  /ws/matches/:id/ │
                  └───────┬───────┴───────┬──────────┘
                          │               │
          ┌───────────────┘               └─────────────────┐
          ▼                                                  ▼
┌──────────────────────┐                      ┌─────────────────────────┐
│   PostgreSQL 15       │                      │       Redis 7           │
│   (persistent data)   │                      │  - Channel layers       │
└──────────────────────┘                      │  - Celery broker        │
                                              │  - Django cache         │
                                              └────────────┬────────────┘
                                                           │
                                              ┌────────────┴────────────┐
                                              │  Celery Worker + Beat   │
                                              │  - Auto start matches   │
                                              │  - Auto finish matches  │
                                              │  - Cleanup audit logs   │
                                              └─────────────────────────┘
```

---

## Getting Started (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 running locally
- Redis 7 running locally

On macOS with Homebrew:
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

### 1. Clone the repository

```bash
git clone https://github.com/tasim313/Multi-Sport-Portal-with-Live-Streaming-using-Django-Full-Stack.git
cd Multi-Sport-Portal-with-Live-Streaming-using-Django-Full-Stack
```

### 2. Set up Python virtual environment

```bash
python3.11 -m venv venv_new
source venv_new/bin/activate        # Linux/Mac
venv_new\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Create the database

```bash
createdb -U postgres sports_portal
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Load sample data

```bash
python manage.py shell < load_sample_data.py
```

This creates:
- 3 sports: Cricket, Football, Tennis
- 3 leagues: IPL, EPL, ATP
- 6 teams: MI, CSK, RCB, KKR, Man Utd, Arsenal
- Sample matches (1 live, 2 upcoming)
- **Admin user: username=`admin`, password=`admin123`**

### 6. Start the Django backend

```bash
python manage.py runserver
# Running on http://localhost:8000
```

### 7. Install and start the React frontend

```bash
npm install
npm run dev
# Running on http://localhost:5173
```

### 8. (Optional) Start Celery for background tasks

```bash
# Worker + Beat scheduler in one process (development only)
python -m celery -A sports_portal worker -B --loglevel=info
```

---

## Environment Variables

Create a `.env` file in the project root (never commit this file):

```env
SECRET_KEY=replace-with-a-long-random-string-50-chars-minimum
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=sports_portal
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

WAGTAIL_BASE_URL=http://localhost:8000
```

For **production**, set `DEBUG=False` — this automatically activates:
- `SECURE_SSL_REDIRECT = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 year)
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`

---

## Running with Docker

```bash
docker-compose up --build
```

Services started:

| Service | Description | Port |
|---------|-------------|------|
| `db` | PostgreSQL 15 | 5432 |
| `redis` | Redis 7 | 6379 |
| `web` | Django + Daphne | 8000 |
| `celery` | Celery Worker | — |
| `celery-beat` | Celery Scheduler | — |
| `nginx` | Reverse Proxy | 80 |

Access points:

| URL | Description |
|-----|-------------|
| http://localhost | React frontend |
| http://localhost/api/ | REST API |
| http://localhost/api/docs/ | Swagger UI |
| http://localhost/django-admin/ | Django Admin |
| http://localhost/cms-admin/ | Wagtail CMS |

---

## API Reference

Interactive Swagger documentation: **http://localhost:8000/api/docs/**
OpenAPI 3 schema (JSON): **http://localhost:8000/api/schema/**

### Authentication

All write endpoints and premium content require a JWT Bearer token:

```
Authorization: Bearer <access_token>
```

#### Get a token

```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

Response:
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

#### Refresh a token

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{ "refresh": "<refresh_token>" }
```

#### Register a new account

```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john",
  "email": "john@example.com",
  "password": "securepass123"
}
```

---

### Sports

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/sports/` | No | List all active sports |
| GET | `/api/sports/{id}/` | No | Single sport detail |

---

### Leagues

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/leagues/` | No | List all leagues |
| GET | `/api/leagues/?sport=cricket` | No | Filter by sport slug |
| GET | `/api/leagues/{id}/` | No | Single league detail |

---

### Teams

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/teams/` | No | List all teams |
| GET | `/api/teams/?league=ipl` | No | Filter by league slug |
| GET | `/api/teams/{id}/` | No | Single team detail |

---

### Matches

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/matches/` | No | List all matches |
| GET | `/api/matches/?status=live` | No | Filter: `live`, `upcoming`, `finished` |
| GET | `/api/matches/?sport=cricket` | No | Filter by sport slug |
| GET | `/api/matches/?league=ipl` | No | Filter by league slug |
| GET | `/api/matches/{id}/` | No | Match detail |
| GET | `/api/matches/{id}/streams/` | Optional* | Best active stream for this match |
| GET | `/api/matches/{id}/events/` | No | Score event history |
| GET | `/api/live-matches/` | No | Currently live matches (max 10) |
| GET | `/api/upcoming-matches/` | No | Scheduled future matches (max 20) |
| GET | `/api/standings/?league=ipl` | No | League standings table |

> *Unauthenticated users only see streams where `requires_auth=False`

---

### Articles (News)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/articles/` | No | List published articles |
| GET | `/api/articles/{slug}/` | No | Article detail by slug |

---

### Score Events (Write)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/matches/{id}/events/` | Yes (editor+) | Create score event + broadcast WebSocket |

Request body:
```json
{
  "event_type": "goal",
  "period": "first_half",
  "payload": { "scorer": "Rashford", "minute": 34 }
}
```

Event types: `goal`, `wicket`, `boundary`, `substitution`, `card`, `period_start`, `period_end`, `other`

---

### Ads

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/ads/?slot=header_banner&device=desktop` | No | Active creatives for a slot |

`device` values: `all`, `desktop`, `mobile`, `tablet`

---

### Search

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/search/?q=manchester` | No | Search matches, articles, teams (min 2 chars) |

Response:
```json
{
  "matches": [...],
  "articles": [...],
  "teams": [...]
}
```

---

### User Profile

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/auth/profile/` | Yes | Get logged-in user profile |
| PATCH | `/api/auth/profile/` | Yes | Update `favorite_teams` or `notification_prefs` |

PATCH body (only these two fields are writable):
```json
{
  "favorite_teams": ["MI", "ManUtd"],
  "notification_prefs": { "email": true, "push": false }
}
```

---

## WebSocket Events

Connect to a match room to receive live updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/matches/1/');

ws.onopen = () => console.log('Connected to match room');

ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);

    switch (msg.type) {
        case 'match_data':
            // Sent immediately on connect — full match state
            console.log(msg.data);
            break;

        case 'score_update':
            // A new score event was created (goal, wicket, etc.)
            // { id, timestamp, period, event_type, payload }
            console.log(msg.data);
            break;

        case 'match_status_update':
            // Match status changed (scheduled→live, live→finished, etc.)
            // { match_id, status }
            console.log(msg.data);
            break;
    }
};

ws.onclose = () => console.log('Disconnected from match room');
```

---

## User Roles & Permissions

| Role | Streams | Write Score Events | Manage Matches | Full Admin |
|------|---------|-------------------|----------------|------------|
| `anonymous` | Public only | No | No | No |
| `registered` | Public + auth-required | No | No | No |
| `subscriber` | All (premium) | No | No | No |
| `editor` | All | Yes | No | No |
| `streamer_admin` | All | Yes | Yes | No |
| `sysadmin` | All | Yes | Yes | Yes |

Roles are set in Django Admin → Users → Role field.

---

## Admin Panels

### Django Admin — `http://localhost:8000/django-admin/`

| Section | What you can do |
|---------|----------------|
| Users | Create users, set roles, toggle premium |
| Sports / Leagues / Teams | Manage sports structure |
| Matches | Create matches with inline streams and score events |
| Stream Sources | Add YouTube/Vimeo/custom embed URLs with security config |
| Articles | Create/edit news articles |
| Ad Placements | Configure ad slots and upload creatives |
| Audit Log | Read-only log of all admin actions (actor, IP, before/after data) |

### Wagtail CMS — `http://localhost:8000/cms-admin/`

| Section | What you can do |
|---------|----------------|
| Pages | Build page tree (HomePage, SportPage, NewsArticlePage) |
| Site Settings | Edit global site info, contact details, social links |
| Advertisements | Manage banner creatives shown on CMS pages |
| Live Match Widgets | Embed live match widgets into CMS pages |

**Login:** `admin` / `admin123`

---

## Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Hero banner + live matches + upcoming matches + latest news |
| `/sport/:sport` | Sport | Matches for one sport, filtered by live / upcoming / finished |
| `/live` | Live | All live matches across all sports |
| `/match/:id` | Match Detail | Embedded stream + score events tab + WebSocket real-time updates |
| `/news` | News | Published article listing |
| `/news/:slug` | Article | Full article detail page |
| `/search?q=` | Search | Live search across matches, articles, and teams |
| `/login` | Login | JWT login form with token storage |
| `/register` | Register | New account registration |
| `/profile` | Profile | User info, favourite teams editor, premium subscription CTA |

Legacy sport redirects: `/cricket` → `/sport/cricket`, `/football` → `/sport/football`, `/tennis` → `/sport/tennis`

---

## Real-Time Score Updates Flow

```
1. Editor opens a live match in the browser
2. Editor calls: POST /api/matches/{id}/events/
   Body: { "event_type": "goal", "period": "2nd half", "payload": {...} }

3. Django saves ScoreEvent to PostgreSQL

4. Django calls:
   channel_layer.group_send("match_{id}", {
       "type": "score_update",
       "data": { ...score event data... }
   })

5. Redis distributes message to all Channels consumers for this match

6. MatchConsumer.score_update() sends WebSocket frame to every
   connected browser watching this match

7. React receives the message and updates the score display instantly
   — no page reload required
```

---

## Celery Background Tasks

| Task | Schedule | What it does |
|------|----------|-------------|
| `auto_start_matches` | Every 60s | Changes `scheduled → live` when `start_time` has passed; broadcasts `match_status_update` via WebSocket |
| `auto_finish_matches` | Every 60s | Changes `live → finished` when `end_time` has passed; broadcasts status update |
| `cleanup_old_audit_logs` | Daily 2am UTC | Deletes `AuditLog` entries older than 90 days |

---

## Deployment Checklist

- [ ] Set `DEBUG=False` and a strong `SECRET_KEY` in `.env`
- [ ] Set `ALLOWED_HOSTS` to your production domain
- [ ] Configure SSL certificate (Let's Encrypt recommended)
- [ ] Run `python manage.py collectstatic`
- [ ] Set up automated PostgreSQL backups
- [ ] Configure Sentry (or similar) for error tracking
- [ ] Set resource limits on Docker containers
- [ ] Rotate JWT secret or use asymmetric keys for production

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes with a clear message
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request targeting `main`

---

## License

MIT License — see [LICENSE](LICENSE) for details.
