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
    avatar = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    watch_history = models.JSONField(default=list, blank=True)  # [{match_id, watched_at}]
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
    colors = models.JSONField(default=dict, blank=True)
    country = models.CharField(max_length=100, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.short_name})"

    class Meta:
        unique_together = ['league', 'slug']
        ordering = ['name']


class PlayerProfile(models.Model):
    """Player profile data"""
    POSITION_CHOICES = [
        ('goalkeeper', 'Goalkeeper'),
        ('defender', 'Defender'),
        ('midfielder', 'Midfielder'),
        ('forward', 'Forward'),
        ('batsman', 'Batsman'),
        ('bowler', 'Bowler'),
        ('all_rounder', 'All-Rounder'),
        ('wicket_keeper', 'Wicket Keeper'),
        ('singles', 'Singles Player'),
        ('doubles', 'Doubles Player'),
        ('other', 'Other'),
    ]

    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='players')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    nationality = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True)
    jersey_number = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.URLField(blank=True)
    stats = models.JSONField(default=dict, blank=True)  # {"goals": 10, "assists": 5}
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.team})"

    class Meta:
        ordering = ['name']


class LeagueTable(models.Model):
    """League standings/table row"""
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='table_rows')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='table_entries')
    season = models.CharField(max_length=50)
    position = models.IntegerField(default=0)
    played = models.IntegerField(default=0)
    won = models.IntegerField(default=0)
    drawn = models.IntegerField(default=0)
    lost = models.IntegerField(default=0)
    goals_for = models.IntegerField(default=0)
    goals_against = models.IntegerField(default=0)
    goal_difference = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    form = models.CharField(max_length=10, blank=True)  # e.g. WWDLW
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.league.name} - {self.team.name} (Pos: {self.position})"

    class Meta:
        unique_together = ['league', 'team', 'season']
        ordering = ['position']


class UserFavorite(models.Model):
    """User favorites: teams and IPTV channels"""
    ITEM_TYPE_CHOICES = [
        ('team', 'Team'),
        ('channel', 'IPTV Channel'),
        ('league', 'League'),
        ('player', 'Player'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    item_id = models.IntegerField()
    item_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.item_type}:{self.item_id}"

    class Meta:
        unique_together = ['user', 'item_type', 'item_id']
        ordering = ['-created_at']


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

    score_summary = models.JSONField(default=dict, blank=True)
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
        ('hls', 'HLS/M3U8'),
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('akamai', 'Akamai CDN'),
        ('custom', 'Custom/ISP'),
        ('iframe', 'iFrame Embed'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='stream_sources')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    url = models.URLField(validators=[URLValidator()], max_length=2000)
    embed_html = models.TextField(blank=True)

    is_iframe = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    requires_auth = models.BooleanField(default=False)

    allowed_domains = models.JSONField(default=list, blank=True)
    geo_whitelist = models.JSONField(default=list, blank=True)
    sandbox_flags = models.JSONField(default=list, blank=True)

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


class IPTVChannel(models.Model):
    """Public IPTV channel metadata imported from external playlist sources."""
    CATEGORY_CHOICES = [
        ('Sports', 'Sports'),
        ('Entertainment', 'Entertainment'),
        ('Movies', 'Movies'),
        ('Kids', 'Kids'),
        ('Music', 'Music'),
        ('News', 'News'),
        ('International', 'International'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    stream_url = models.URLField(validators=[URLValidator()], max_length=2000)
    source_id = models.CharField(max_length=300, unique=True)
    source_name = models.CharField(max_length=100, default='iptv-org')
    source_url = models.URLField(max_length=1000, blank=True)

    tvg_id = models.CharField(max_length=255, blank=True)
    logo = models.URLField(max_length=1000, blank=True)
    category = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    country_code = models.CharField(max_length=12, blank=True)
    language = models.CharField(max_length=120, blank=True)

    # Stream health
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    last_checked = models.DateTimeField(null=True, blank=True)
    is_working = models.BooleanField(default=True)

    imported_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['category', 'country_code']),
            models.Index(fields=['is_active', 'is_featured']),
        ]


class EPGProgram(models.Model):
    """Electronic Program Guide data for IPTV channels"""
    channel = models.ForeignKey(IPTVChannel, on_delete=models.CASCADE, related_name='epg_programs')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    category = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, blank=True)
    icon = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel.name}: {self.title} ({self.start_time})"

    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['channel', 'start_time', 'end_time']),
        ]


class ScoreEvent(models.Model):
    """Real-time score events during matches"""
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('wicket', 'Wicket'),
        ('boundary', 'Boundary'),
        ('six', 'Six'),
        ('substitution', 'Substitution'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('period_start', 'Period Start'),
        ('period_end', 'Period End'),
        ('penalty', 'Penalty'),
        ('injury', 'Injury'),
        ('var_check', 'VAR Check'),
        ('other', 'Other'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='score_events')
    timestamp = models.DateTimeField(default=timezone.now)
    period = models.CharField(max_length=50, blank=True)
    minute = models.IntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    payload = models.JSONField(default=dict)
    player_name = models.CharField(max_length=200, blank=True)
    team_side = models.CharField(max_length=10, blank=True, choices=[('home', 'Home'), ('away', 'Away')])

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.match} - {self.event_type} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class LiveCommentary(models.Model):
    """AI-rewritten live commentary for matches"""
    SOURCE_CHOICES = [
        ('manual', 'Manual Entry'),
        ('crawled', 'Crawled/Scraped'),
        ('ai', 'AI Generated'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='commentary')
    minute = models.IntegerField(null=True, blank=True)
    period = models.CharField(max_length=50, blank=True)

    original_text = models.TextField(blank=True)
    rewritten_text = models.TextField()

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    language = models.CharField(max_length=10, default='en')
    is_key_event = models.BooleanField(default=False)

    score_event = models.OneToOneField(
        ScoreEvent, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='commentary'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.match} - {self.minute}' - {self.rewritten_text[:80]}"

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Live Commentary'


class Article(models.Model):
    """News articles and editorial content"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    CATEGORY_CHOICES = [
        ('news', 'News'),
        ('preview', 'Match Preview'),
        ('review', 'Match Review'),
        ('highlight', 'Highlights'),
        ('transfer', 'Transfer News'),
        ('analysis', 'Analysis'),
        ('interview', 'Interview'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    body = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)

    author = models.ForeignKey(
        'sports.User', on_delete=models.SET_NULL, null=True, related_name='articles'
    )
    sport = models.ForeignKey(Sport, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    hero_image = models.URLField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='news')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)

    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=300, blank=True)
    views_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at', '-created_at']


class AdPlacement(models.Model):
    """Ad placement configuration"""
    AD_TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('video', 'Video'),
        ('popup', 'Popup'),
        ('sidebar', 'Sidebar'),
        ('interstitial', 'Interstitial'),
    ]

    DEVICE_CHOICES = [
        ('all', 'All Devices'),
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ]

    slot_key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=200)
    ad_type = models.CharField(max_length=20, choices=AD_TYPE_CHOICES, default='banner')
    device_target = models.CharField(max_length=20, choices=DEVICE_CHOICES, default='all')
    path_pattern = models.CharField(max_length=200, default='*')
    is_active = models.BooleanField(default=True)
    rotation_interval = models.IntegerField(default=30, help_text='Seconds between ad rotation')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} ({self.slot_key})"


class AdCreative(models.Model):
    """Individual ad creatives"""
    placement = models.ForeignKey(AdPlacement, on_delete=models.CASCADE, related_name='creatives')
    name = models.CharField(max_length=200)
    html_snippet = models.TextField()
    image_url = models.URLField(blank=True)
    click_url = models.URLField(blank=True)

    start_at = models.DateTimeField(default=timezone.now)
    end_at = models.DateTimeField(null=True, blank=True)

    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
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
