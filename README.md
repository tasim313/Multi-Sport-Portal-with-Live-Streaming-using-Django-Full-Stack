# Django Sports Portal

A comprehensive, secure, and high-performance sports web application supporting cricket, football, tennis, and more, with live streaming, real-time updates, monetization via ads/sponsorships, and role-based governance.

## Features

### Core Functionality
- **Multi-Sport Support**: Cricket, Football, Tennis with extensible architecture
- **Live Streaming**: Secure embed management for YouTube, Vimeo, CDN, and custom ISP links
- **Real-Time Updates**: WebSocket-powered live score updates and match events
- **Role-Based Access**: Anonymous, Registered, Subscriber, Editor, Streamer Admin, SysAdmin
- **Monetization**: Ad placement system with rotation/capping rules and subscription model

### Technical Highlights
- **Backend**: Django 5 + Django REST Framework + PostgreSQL
- **Frontend**: React + Tailwind CSS + React Query
- **Real-Time**: Django Channels + Redis WebSockets
- **Security**: CSP, iframe sandboxing, JWT authentication, audit logging
- **Deployment**: Docker + docker-compose ready

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Development Setup

1. **Clone and Setup Backend**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Setup database
createdb sports_portal
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py shell < load_sample_data.py

# Start Django server
python manage.py runserver
```

2. **Setup Frontend**
```bash
# Install Node dependencies
npm install

# Start development server
npm run dev
```

3. **Start Redis** (for WebSockets)
```bash
redis-server
```

### Docker Setup

```bash
# Build and start all services
docker-compose up --build

# The application will be available at:
# - Frontend: http://localhost
# - API: http://localhost:8000/api/
# - Admin: http://localhost:8000/admin/
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/

### Key Endpoints

```
GET /api/sports/                    # List all sports
GET /api/leagues/?sport=cricket     # Leagues by sport
GET /api/matches/?status=live       # Live matches
GET /api/matches/{id}/streams/      # Match streams
GET /api/articles/                  # News articles
WS  /ws/matches/{id}/              # Real-time match updates
```

## Architecture

### Backend Models
- **Sport, League, Team, Player, Venue**: Core sports entities
- **Match, StreamSource, ScoreEvent**: Live match management
- **Article, AdPlacement, AdCreative**: Content and monetization
- **User, UserProfile, AuditLog**: Authentication and governance

### Security Features
- **CSP Headers**: Strict content security policy for iframe safety
- **Iframe Sandboxing**: Configurable sandbox flags for stream embeds
- **JWT Authentication**: Secure API access with refresh tokens
- **Audit Logging**: Complete admin action trail
- **Rate Limiting**: Django-axes for brute force protection

### Real-Time Architecture
```
Browser WebSocket ←→ Django Channels ←→ Redis ←→ Celery Workers
                                    ↓
                              PostgreSQL Database
```

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in settings
- [ ] Configure proper `SECRET_KEY`
- [ ] Setup SSL certificates (Let's Encrypt)
- [ ] Configure NGINX reverse proxy
- [ ] Setup Sentry for error tracking
- [ ] Configure Prometheus/Grafana monitoring
- [ ] Setup automated backups

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DB_PASSWORD=secure-password
REDIS_URL=redis://redis:6379/0
```

## Admin Panel

Access the Django admin at `/admin/` to:
- Manage sports, leagues, teams, and matches
- Add/configure live stream sources with security validation
- Create and schedule articles
- Configure ad placements and creatives
- Monitor user activity via audit logs

### Stream Management
1. Create a match with teams and schedule
2. Add StreamSource with provider (YouTube/Vimeo/Custom)
3. Paste embed URL or full HTML iframe code
4. Configure security: allowed domains, geo restrictions, sandbox flags
5. Set priority and activate stream

## Development

### Project Structure
```
sports_portal/
├── sports/                 # Main Django app
│   ├── models.py          # Database models
│   ├── views.py           # API views and WebSocket consumers
│   ├── admin.py           # Admin interface
│   └── consumers.py       # WebSocket consumers
├── frontend/              # React application
│   ├── src/
│   │   ├── App.jsx       # Main React component
│   │   └── components.jsx # Reusable UI components
│   └── public/
├── requirements.txt       # Python dependencies
├── package.json          # Node.js dependencies
└── docker-compose.yml    # Docker configuration
```

### Adding New Sports
1. Create Sport record in admin
2. Add leagues and teams
3. Configure match schedules
4. Update frontend navigation (optional)

### WebSocket Events
```javascript
// Connect to match updates
const ws = new WebSocket(`ws://localhost:8000/ws/matches/${matchId}/`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'score_update') {
        // Handle real-time score update
        updateMatchScore(data.data);
    }
};
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the API documentation
- Review the admin panel help text