from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import URLValidator
from django.utils import timezone


class User(AbstractUser):
    """Extended user model with sports portal specific fields"""
    ROLE_CHOICES = [
        ('anonymous', 'Anonymous'),
        ('registered', 'Registered'),
        ('subscriber', 'Subscriber'),
        ('editor', 'Editor'),
        ('streamer_admin', 'Streamer Admin'),
        ('sysadmin', 'System Admin'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='registered')
    favorite_teams = models.JSONField(default=list, blank=True)
    notification_prefs = models.JSONField(default=dict, blank=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Sport(models.Model):
    """Sports categories like Cricket, Football, Tennis"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class League(models.Model):
    """Leagues/tournaments within sports"""
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='leagues')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    season = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    logo = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sport.name})"

    class Meta:
        unique_together = ['sport', 'slug']
        ordering = ['sport__name', 'name']


class Team(models.Model):
    """Teams participating in leagues"""
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=10)
    slug = models.SlugField(max_length=200)
    logo = models.URLField(blank=True)
    colors = models.JSONField(default=dict, blank=True)  # {"primary": "#FF0000", "secondary": "#FFFFFF"}
    country = models.CharField(max_length=100, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.short_name})"

    class Meta:
        unique_together = ['league', 'slug']
        ordering = ['name']


class Venue(models.Model):
    """Match venues/stadiums"""
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    capacity = models.IntegerField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}, {self.city}"

    class Meta:
        unique_together = ['name', 'city']
        ordering = ['country', 'city', 'name']


class Match(models.Model):
    """Individual matches/games"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('live', 'Live'),
        ('finished', 'Finished'),
        ('postponed', 'Postponed'),
        ('cancelled', 'Cancelled'),
    ]

    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='matches')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Score summary as JSON: {"home": 2, "away": 1, "details": {...}}
    score_summary = models.JSONField(default=dict, blank=True)

    # Additional match metadata
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.home_team.short_name} vs {self.away_team.short_name} - {self.start_time.date()}"

    class Meta:
        ordering = ['-start_time']
        verbose_name_plural = 'Matches'


class StreamSource(models.Model):
    """Live stream sources for matches"""
    PROVIDER_CHOICES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('akamai', 'Akamai CDN'),
        ('custom', 'Custom/ISP'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='stream_sources')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    url = models.URLField(validators=[URLValidator()])
    embed_html = models.TextField(blank=True)  # Full iframe HTML

    is_iframe = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False)

    # Security and geo settings
    allowed_domains = models.JSONField(default=list, blank=True)
    geo_whitelist = models.JSONField(default=list, blank=True)  # Country codes
    sandbox_flags = models.JSONField(default=list, blank=True)  # iframe sandbox flags

    priority = models.IntegerField(default=1)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'sports.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.match} - {self.provider} (Priority: {self.priority})"

    class Meta:
        ordering = ['-priority', '-created_at']


class ScoreEvent(models.Model):
    """Real-time score events during matches"""
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('wicket', 'Wicket'),
        ('boundary', 'Boundary'),
        ('substitution', 'Substitution'),
        ('card', 'Card'),
        ('period_start', 'Period Start'),
        ('period_end', 'Period End'),
        ('other', 'Other'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='score_events')
    timestamp = models.DateTimeField(default=timezone.now)
    period = models.CharField(max_length=50, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)

    # Event details as JSON: {"player": "John Doe", "team": "home", "minute": 45}
    payload = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.match} - {self.event_type} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class Article(models.Model):
    """News articles and editorial content"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    body = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)

    author = models.ForeignKey(
        'sports.User', on_delete=models.SET_NULL, null=True, related_name='articles'
    )
    tags = models.JSONField(default=list, blank=True)
    hero_image = models.URLField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)

    meta_description = models.CharField(max_length=160, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']


class AdPlacement(models.Model):
    """Ad placement configuration"""
    DEVICE_CHOICES = [
        ('all', 'All Devices'),
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ]

    slot_key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    device_target = models.CharField(max_length=20, choices=DEVICE_CHOICES, default='all')
    path_pattern = models.CharField(max_length=200, default='*')
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} ({self.slot_key})"


class AdCreative(models.Model):
    """Individual ad creatives"""
    placement = models.ForeignKey(AdPlacement, on_delete=models.CASCADE, related_name='creatives')
    name = models.CharField(max_length=200)
    html_snippet = models.TextField()

    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)

    capping_rules = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.placement.label}"


class AuditLog(models.Model):
    """Audit trail for admin actions"""
    actor = models.ForeignKey(
        'sports.User', on_delete=models.SET_NULL, null=True
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)

    before_data = models.JSONField(default=dict, blank=True)
    after_data = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} - {self.action} on {self.object_type}#{self.object_id}"

    class Meta:
        ordering = ['-timestamp']
