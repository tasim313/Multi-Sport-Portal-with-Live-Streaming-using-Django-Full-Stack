#!/usr/bin/env bash
# ─── SportPortal Full Stack Starter ────────────────────────────────────────
# Starts: Django (Daphne ASGI) + Celery Worker + Celery Beat + Next.js Dev
# Prerequisites: PostgreSQL + Redis already running (brew services)
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/venv_new/bin/python3.11"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SportPortal — Starting all services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Check prerequisites ─────────────────────────────────────────────────
echo "[1/5] Checking PostgreSQL..."
if ! pg_isready -q; then
  echo "  PostgreSQL not running. Starting..."
  brew services start postgresql@15
  sleep 2
fi
echo "  PostgreSQL: OK"

echo "[2/5] Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
  echo "  Redis not running. Starting..."
  brew services start redis
  sleep 1
fi
echo "  Redis: OK"

# ── 2. Django migrations ────────────────────────────────────────────────────
echo "[3/5] Running migrations..."
cd "$PROJECT_DIR"
$PYTHON manage.py migrate --settings=sports_portal.settings --no-input 2>&1 | grep -E "Apply|OK|No migrations"

# ── 3. Collect static files ─────────────────────────────────────────────────
echo "[4/5] Collecting static files..."
$PYTHON manage.py collectstatic --settings=sports_portal.settings --no-input -v 0 2>&1 | tail -1

# ── 4. Create superuser if not exists ──────────────────────────────────────
echo "[5/5] Ensuring admin user exists..."
$PYTHON manage.py shell --settings=sports_portal.settings -c "
from sports.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@sportsportal.com','admin123',role='sysadmin')
    print('  Created admin/admin123')
else:
    print('  Admin already exists')
" 2>&1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting services (press Ctrl+C to stop all)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill any existing processes on our ports
lsof -ti:8004 | xargs kill -9 2>/dev/null || true
lsof -ti:3004 | xargs kill -9 2>/dev/null || true
sleep 1

# ── 5. Start Django (Daphne ASGI) ──────────────────────────────────────────
echo "  [Django]  http://localhost:8004"
cd "$PROJECT_DIR"
$PYTHON -m daphne -b 0.0.0.0 -p 8004 sports_portal.asgi:application \
  > "$LOG_DIR/django.log" 2>&1 &
DJANGO_PID=$!

sleep 2

# ── 6. Start Celery Worker ─────────────────────────────────────────────────
echo "  [Celery]  Worker (concurrency 2)"
cd "$PROJECT_DIR"
$PROJECT_DIR/venv_new/bin/celery -A sports_portal worker \
  --loglevel=warning --concurrency=2 \
  > "$LOG_DIR/celery.log" 2>&1 &
CELERY_PID=$!

# ── 7. Start Celery Beat ───────────────────────────────────────────────────
echo "  [Beat]    Scheduler"
cd "$PROJECT_DIR"
$PROJECT_DIR/venv_new/bin/celery -A sports_portal beat \
  --loglevel=warning \
  > "$LOG_DIR/beat.log" 2>&1 &
BEAT_PID=$!

# ── 8. Start Next.js Dev ───────────────────────────────────────────────────
echo "  [Next.js] http://localhost:3004"
cd "$PROJECT_DIR/frontend"
npm run dev > "$LOG_DIR/nextjs.log" 2>&1 &
NEXT_PID=$!

echo ""
echo "  All services started!"
echo ""
echo "  URLs:"
echo "    Frontend:    http://localhost:3004"
echo "    API:         http://localhost:8004/api/"
echo "    API Docs:    http://localhost:8004/api/docs/"
echo "    Django Admin: http://localhost:8004/django-admin/"
echo "    Wagtail CMS:  http://localhost:8004/cms-admin/"
echo "    Admin login:  admin / admin123"
echo ""
echo "  Logs in: $LOG_DIR/"
echo ""
echo "  Press Ctrl+C to stop all services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Trap Ctrl+C to kill all child processes
cleanup() {
  echo ""
  echo "  Stopping all services..."
  kill $DJANGO_PID $CELERY_PID $BEAT_PID $NEXT_PID 2>/dev/null || true
  echo "  Done."
  exit 0
}
trap cleanup INT TERM

# Wait for all background processes
wait
