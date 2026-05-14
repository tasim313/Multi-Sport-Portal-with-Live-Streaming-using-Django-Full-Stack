# SportPortal — AWS EC2 Deployment Guide

## Prerequisites

- AWS account with EC2 access
- Domain name (optional but recommended for SSL)
- Docker Hub account (for image registry)
- GitHub repository secrets configured (for CI/CD)

---

## 1. Launch EC2 Instance

**Recommended specs:**
- Instance type: `t3.medium` (2 vCPU, 4 GB RAM) minimum; `t3.large` for production
- AMI: Ubuntu 22.04 LTS (64-bit x86)
- Storage: 30 GB gp3 SSD
- Security Group inbound rules:
  - TCP 22 (SSH) — your IP only
  - TCP 80 (HTTP) — 0.0.0.0/0
  - TCP 443 (HTTPS) — 0.0.0.0/0

**Create key pair:** Download `sportportal.pem` and set permissions:
```bash
chmod 400 sportportal.pem
```

---

## 2. Connect & Install Dependencies

```bash
ssh -i sportportal.pem ubuntu@<EC2_PUBLIC_IP>
```

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
newgrp docker

# Install Docker Compose v2
sudo apt-get install -y docker-compose-plugin

# Verify
docker --version
docker compose version
```

---

## 3. Clone the Repository

```bash
git clone https://github.com/<your-org>/sports-portal.git
cd sports-portal
```

---

## 4. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

**Minimum required values for production:**

```env
# Django
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
DEBUG=False
ALLOWED_HOSTS=<your-ec2-ip>,<your-domain.com>

# Database
DB_NAME=sports_portal
DB_USER=postgres
DB_PASSWORD=<strong-random-password>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# AI APIs (at least one for commentary rewriting)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Sports data APIs (free tiers available)
FOOTBALL_DATA_API_KEY=...
CRICKET_API_KEY=...

# Wagtail
WAGTAIL_BASE_URL=https://<your-domain.com>

# Frontend
NEXT_PUBLIC_API_URL=https://<your-domain.com>/api
NEXT_PUBLIC_WS_URL=wss://<your-domain.com>

# Monitoring (optional)
SENTRY_DSN=https://...@sentry.io/...
```

---

## 5. Build and Start All Services

```bash
# Build images (first time, takes ~5 minutes)
docker compose build

# Start all services in background
docker compose up -d

# Verify all containers are running
docker compose ps
```

Expected output:
```
NAME                STATUS
sportportal-db      running
sportportal-redis   running
sportportal-web     running
sportportal-celery  running
sportportal-beat    running
sportportal-front   running
sportportal-nginx   running
```

---

## 6. Initialize the Database

```bash
# Run migrations
docker compose exec web python manage.py migrate --settings=sports_portal.settings

# Create superuser
docker compose exec web python manage.py createsuperuser --settings=sports_portal.settings

# Load sample data (optional)
docker compose exec web python manage.py shell --settings=sports_portal.settings < load_sample_data.py

# Collect static files
docker compose exec web python manage.py collectstatic --no-input --settings=sports_portal.settings
```

---

## 7. Import IPTV Channels

Run the initial IPTV import (imports ~1500+ sports/news/entertainment channels):

```bash
docker compose exec web python manage.py shell --settings=sports_portal.settings -c "
from iptv_importer.tasks import import_iptv_playlist
from iptv_importer.m3u_parser import IPTV_ORG_PLAYLISTS
for cat, url in IPTV_ORG_PLAYLISTS.items():
    result = import_iptv_playlist(url, category_override=cat.title())
    print(f'{cat}: {result}')
"
```

After this, Celery Beat will automatically re-sync every night at 3 AM and check stream health every 4 hours.

---

## 8. Configure SSL with Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt-get install -y certbot

# Stop nginx temporarily
docker compose stop nginx

# Get certificate
sudo certbot certonly --standalone -d <your-domain.com> -d www.<your-domain.com>

# Certificates will be at:
# /etc/letsencrypt/live/<your-domain.com>/fullchain.pem
# /etc/letsencrypt/live/<your-domain.com>/privkey.pem
```

Update `nginx.conf` to add HTTPS server block:

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of your location blocks
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$host$request_uri;
}
```

Mount the cert directory in `docker-compose.yml`:

```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
```

Auto-renew via cron:
```bash
sudo crontab -e
# Add:
0 3 * * * certbot renew --quiet && docker compose -f /home/ubuntu/sports-portal/docker-compose.yml restart nginx
```

---

## 9. GitHub Actions CI/CD Setup

Add these secrets to your GitHub repository (`Settings → Secrets → Actions`):

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |
| `EC2_HOST` | Your EC2 public IP |
| `EC2_USER` | `ubuntu` |
| `EC2_SSH_KEY` | Contents of `sportportal.pem` |

The CI/CD pipeline (`.github/workflows/ci.yml`) will:
1. Run Django checks and Next.js build on every push
2. Build and push Docker images on merge to `main`
3. SSH into EC2 and deploy the new images automatically

---

## 10. Monitoring & Maintenance

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f nginx
```

### Health check
```bash
# Django API
curl http://localhost/api/sports/

# Check Celery is processing tasks
docker compose exec celery celery -A sports_portal inspect active

# Check Beat schedule
docker compose exec beat celery -A sports_portal beat --loglevel=info --dry-run
```

### Restart a service
```bash
docker compose restart web
docker compose restart celery
```

### Update deployment
```bash
git pull origin main
docker compose build web frontend
docker compose up -d --no-deps web frontend
docker compose exec web python manage.py migrate --settings=sports_portal.settings
```

### Database backup
```bash
# Backup
docker compose exec db pg_dump -U postgres sports_portal > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U postgres sports_portal < backup_20260514.sql
```

---

## 11. Performance Tuning

### Scale Celery workers
```bash
# Run 4 concurrent workers
docker compose up -d --scale celery=2
```

Or in `docker-compose.yml`:
```yaml
celery:
  command: celery -A sports_portal worker --loglevel=warning --concurrency=4
```

### PostgreSQL connection pooling
Add `pgbouncer` or use `CONN_MAX_AGE=60` in Django settings (already set).

### Redis memory policy
```bash
docker compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
docker compose exec redis redis-cli CONFIG SET maxmemory 256mb
```

---

## 12. Environment Variable Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key (50+ chars) |
| `DEBUG` | Yes | `False` in production |
| `ALLOWED_HOSTS` | Yes | Comma-separated domains/IPs |
| `DB_NAME` | Yes | PostgreSQL database name |
| `DB_USER` | Yes | PostgreSQL username |
| `DB_PASSWORD` | Yes | PostgreSQL password |
| `DB_HOST` | Yes | `db` in Docker, `localhost` locally |
| `REDIS_URL` | Yes | `redis://redis:6379/0` in Docker |
| `ANTHROPIC_API_KEY` | No | For AI commentary (Tier 1) |
| `OPENAI_API_KEY` | No | For AI commentary (Tier 2 fallback) |
| `FOOTBALL_DATA_API_KEY` | No | Live football scores |
| `CRICKET_API_KEY` | No | Live cricket scores |
| `SENTRY_DSN` | No | Error monitoring |
| `WAGTAIL_BASE_URL` | Yes | Full URL for Wagtail media |
| `NEXT_PUBLIC_API_URL` | Yes | API base URL for frontend |
| `NEXT_PUBLIC_WS_URL` | Yes | WebSocket base URL for frontend |

---

## Access URLs (Production)

| Service | URL |
|---------|-----|
| Frontend | `https://your-domain.com` |
| REST API | `https://your-domain.com/api/` |
| API Docs | `https://your-domain.com/api/docs/` |
| Django Admin | `https://your-domain.com/django-admin/` |
| Wagtail CMS | `https://your-domain.com/cms-admin/` |
| WebSocket | `wss://your-domain.com/ws/matches/<id>/` |
| Score Ticker | `wss://your-domain.com/ws/ticker/` |
