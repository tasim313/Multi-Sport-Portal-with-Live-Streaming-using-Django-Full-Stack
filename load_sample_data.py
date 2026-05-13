"""
Sample data loader for Sports Portal.
Run with: python manage.py shell < load_sample_data.py
"""
import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sports_portal.settings')
django.setup()

from sports.models import Sport, League, Team, Venue, Match, StreamSource, Article, AdPlacement, AdCreative
from django.contrib.auth import get_user_model

User = get_user_model()

print("Creating sample data...")

# ─── Sports ──────────────────────────────────────────────────────────────────
cricket, _ = Sport.objects.get_or_create(
    slug='cricket',
    defaults={'name': 'Cricket', 'icon': '🏏', 'is_active': True}
)
football, _ = Sport.objects.get_or_create(
    slug='football',
    defaults={'name': 'Football', 'icon': '⚽', 'is_active': True}
)
tennis, _ = Sport.objects.get_or_create(
    slug='tennis',
    defaults={'name': 'Tennis', 'icon': '🎾', 'is_active': True}
)
print("Sports created.")

# ─── Leagues ─────────────────────────────────────────────────────────────────
ipl, _ = League.objects.get_or_create(
    sport=cricket, slug='ipl',
    defaults={'name': 'Indian Premier League', 'season': '2025', 'country': 'India', 'is_active': True}
)
psl, _ = League.objects.get_or_create(
    sport=cricket, slug='psl',
    defaults={'name': 'Pakistan Super League', 'season': '2025', 'country': 'Pakistan', 'is_active': True}
)
epl, _ = League.objects.get_or_create(
    sport=football, slug='epl',
    defaults={'name': 'English Premier League', 'season': '2024-25', 'country': 'England', 'is_active': True}
)
atp, _ = League.objects.get_or_create(
    sport=tennis, slug='atp-tour',
    defaults={'name': 'ATP Tour', 'season': '2025', 'country': 'International', 'is_active': True}
)
print("Leagues created.")

# ─── Teams ───────────────────────────────────────────────────────────────────
mi, _ = Team.objects.get_or_create(
    league=ipl, slug='mumbai-indians',
    defaults={
        'name': 'Mumbai Indians', 'short_name': 'MI',
        'colors': {'primary': '#004C97', 'secondary': '#D1AB3E'},
        'country': 'India', 'is_active': True
    }
)
csk, _ = Team.objects.get_or_create(
    league=ipl, slug='chennai-super-kings',
    defaults={
        'name': 'Chennai Super Kings', 'short_name': 'CSK',
        'colors': {'primary': '#FFFF3C', 'secondary': '#0081E9'},
        'country': 'India', 'is_active': True
    }
)
rcb, _ = Team.objects.get_or_create(
    league=ipl, slug='royal-challengers-bangalore',
    defaults={
        'name': 'Royal Challengers Bangalore', 'short_name': 'RCB',
        'colors': {'primary': '#EC1C24', 'secondary': '#000000'},
        'country': 'India', 'is_active': True
    }
)
kkr, _ = Team.objects.get_or_create(
    league=ipl, slug='kolkata-knight-riders',
    defaults={
        'name': 'Kolkata Knight Riders', 'short_name': 'KKR',
        'colors': {'primary': '#3A225D', 'secondary': '#B3A123'},
        'country': 'India', 'is_active': True
    }
)
manu, _ = Team.objects.get_or_create(
    league=epl, slug='manchester-united',
    defaults={
        'name': 'Manchester United', 'short_name': 'MAN UTD',
        'colors': {'primary': '#DA291C', 'secondary': '#FBE122'},
        'country': 'England', 'is_active': True
    }
)
arsenal, _ = Team.objects.get_or_create(
    league=epl, slug='arsenal',
    defaults={
        'name': 'Arsenal', 'short_name': 'ARS',
        'colors': {'primary': '#EF0107', 'secondary': '#FFFFFF'},
        'country': 'England', 'is_active': True
    }
)
print("Teams created.")

# ─── Venues ──────────────────────────────────────────────────────────────────
wankhede, _ = Venue.objects.get_or_create(
    name='Wankhede Stadium', city='Mumbai',
    defaults={'country': 'India', 'capacity': 33000}
)
old_trafford, _ = Venue.objects.get_or_create(
    name='Old Trafford', city='Manchester',
    defaults={'country': 'England', 'capacity': 74310}
)
print("Venues created.")

# ─── Matches ─────────────────────────────────────────────────────────────────
now = timezone.now()

match1, _ = Match.objects.get_or_create(
    league=ipl, home_team=mi, away_team=csk,
    start_time=now - timedelta(hours=1),
    defaults={
        'venue': wankhede,
        'status': 'live',
        'score_summary': {'home': 185, 'away': 142, 'details': {'overs': '18.3'}},
    }
)
match2, _ = Match.objects.get_or_create(
    league=ipl, home_team=rcb, away_team=kkr,
    start_time=now + timedelta(hours=3),
    defaults={
        'venue': wankhede,
        'status': 'scheduled',
        'score_summary': {},
    }
)
match3, _ = Match.objects.get_or_create(
    league=epl, home_team=manu, away_team=arsenal,
    start_time=now + timedelta(days=1),
    defaults={
        'venue': old_trafford,
        'status': 'scheduled',
        'score_summary': {},
    }
)
print("Matches created.")

# ─── Stream Sources ───────────────────────────────────────────────────────────
StreamSource.objects.get_or_create(
    match=match1, provider='youtube',
    defaults={
        'url': 'https://www.youtube.com/embed/live_stream?channel=UCxxxxxxxx',
        'embed_html': '',
        'is_active': True,
        'priority': 1,
        'requires_auth': False,
    }
)
print("Stream sources created.")

# ─── Articles ────────────────────────────────────────────────────────────────
# Create a superuser for article author if not exists
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@sportsportal.com',
        'role': 'sysadmin',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("Admin user created (username: admin, password: admin123)")

Article.objects.get_or_create(
    slug='mi-vs-csk-preview-2025',
    defaults={
        'title': 'MI vs CSK: The Classic Rivalry Returns',
        'body': 'Mumbai Indians and Chennai Super Kings face off in what promises to be an epic encounter. '
                'Both teams have been in top form this season, with MI\'s batting lineup looking particularly '
                'dangerous. CSK will rely on MS Dhoni\'s leadership and experience to guide them through.',
        'excerpt': 'The two most successful IPL franchises clash in another blockbuster encounter.',
        'author': admin_user,
        'tags': ['IPL', 'Cricket', 'MI', 'CSK'],
        'status': 'published',
        'published_at': now - timedelta(hours=2),
    }
)
print("Articles created.")

# ─── Ad Placements ────────────────────────────────────────────────────────────
header_placement, _ = AdPlacement.objects.get_or_create(
    slot_key='header_banner',
    defaults={'label': 'Header Banner', 'device_target': 'all', 'is_active': True}
)
sidebar_placement, _ = AdPlacement.objects.get_or_create(
    slot_key='sidebar_ad',
    defaults={'label': 'Sidebar Advertisement', 'device_target': 'desktop', 'is_active': True}
)

AdCreative.objects.get_or_create(
    placement=header_placement, name='Sample Header Ad',
    defaults={
        'html_snippet': '<div style="background:#0B6E4F;color:#fff;padding:10px;text-align:center;">Sample Advertisement</div>',
        'is_active': True,
    }
)
print("Ad placements created.")

print("\nSample data loaded successfully!")
print("Admin credentials: username=admin, password=admin123")
