#!/bin/bash

# Wait for database
echo "Waiting for database..."
while ! nc -z $DB_HOST 5432; do
  sleep 0.1
done
echo "Database started"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Load initial data
echo "Loading initial data..."
python manage.py shell -c "
from sports.models import Sport, League, Team, Match
import json
from datetime import datetime, timedelta
from django.utils import timezone

# Create sports
sports_data = [
    {'name': 'Cricket', 'slug': 'cricket', 'icon': '🏏'},
    {'name': 'Football', 'slug': 'football', 'icon': '⚽'},
    {'name': 'Tennis', 'slug': 'tennis', 'icon': '🎾'},
]

for sport_data in sports_data:
    sport, created = Sport.objects.get_or_create(
        slug=sport_data['slug'],
        defaults=sport_data
    )
    if created:
        print(f'Created sport: {sport.name}')

# Create sample leagues
cricket = Sport.objects.get(slug='cricket')
football = Sport.objects.get(slug='football')

leagues_data = [
    {'sport': cricket, 'name': 'IPL 2024', 'slug': 'ipl-2024', 'country': 'India'},
    {'sport': cricket, 'name': 'The Ashes', 'slug': 'ashes-2024', 'country': 'England'},
    {'sport': football, 'name': 'Premier League', 'slug': 'premier-league', 'country': 'England'},
    {'sport': football, 'name': 'La Liga', 'slug': 'la-liga', 'country': 'Spain'},
]

for league_data in leagues_data:
    league, created = League.objects.get_or_create(
        slug=league_data['slug'],
        defaults=league_data
    )
    if created:
        print(f'Created league: {league.name}')

print('Initial data loaded successfully')
"

exec "$@"