# Django Sports Portal MVP Implementation Plan

## Core Files to Create (8 files max - HARD LIMIT)

### Backend Django Files (4 files)
1. **requirements.txt** - Django dependencies and packages
2. **settings.py** - Django configuration with security, database, channels
3. **models.py** - Core sports entities (Sport, League, Team, Match, StreamSource, User roles)
4. **views.py** - REST API endpoints and WebSocket consumers

### Frontend React Files (4 files)
5. **package.json** - React/Next.js dependencies
6. **index.html** - Main HTML template with CSP headers
7. **App.jsx** - Main React component with routing and WebSocket
8. **components.jsx** - Reusable UI components (MatchCard, StreamPlayer, etc.)

## MVP Features (Simplified for Success)
- ✅ Basic Django models for Sport, League, Team, Match, StreamSource
- ✅ REST API endpoints for matches, streams, basic CRUD
- ✅ Simple WebSocket for live score updates
- ✅ React frontend with match listing and stream embedding
- ✅ Basic role-based auth (Admin, User)
- ✅ Simple ad placement system
- ✅ Docker setup for deployment

## Excluded from MVP (to ensure completion)
- Complex geo-filtering (basic version only)
- Advanced audit logging (basic version)
- Full subscription system (basic premium flag)
- Complex CSP rules (basic iframe security)
- Prometheus/Grafana (basic logging only)

## Implementation Order
1. Django backend setup with models and basic API
2. React frontend with match display and streaming
3. WebSocket integration for real-time updates
4. Basic authentication and admin features
5. Docker containerization
6. Final testing and deployment setup

This approach prioritizes a working MVP over perfect feature completeness.