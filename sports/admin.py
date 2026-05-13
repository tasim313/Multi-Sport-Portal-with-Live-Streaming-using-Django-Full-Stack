from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, Sport, League, Team, Venue, Match,
    StreamSource, ScoreEvent, Article,
    AdPlacement, AdCreative, AuditLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_premium', 'is_active', 'date_joined')
    list_filter = ('role', 'is_premium', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Sports Portal', {
            'fields': ('role', 'is_premium', 'favorite_teams', 'notification_prefs')
        }),
    )


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'sport', 'season', 'country', 'is_active')
    list_filter = ('sport', 'is_active', 'country')
    search_fields = ('name', 'season')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'league', 'country', 'is_active')
    list_filter = ('league__sport', 'league', 'is_active', 'country')
    search_fields = ('name', 'short_name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country', 'capacity')
    list_filter = ('country',)
    search_fields = ('name', 'city', 'country')


class StreamSourceInline(admin.TabularInline):
    model = StreamSource
    extra = 1
    fields = ('provider', 'url', 'priority', 'is_active', 'requires_auth')


class ScoreEventInline(admin.TabularInline):
    model = ScoreEvent
    extra = 0
    readonly_fields = ('timestamp', 'created_at')
    fields = ('event_type', 'period', 'timestamp', 'payload')


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'league', 'start_time', 'status', 'get_score', 'stream_count')
    list_filter = ('status', 'league__sport', 'league', 'start_time')
    search_fields = ('home_team__name', 'away_team__name', 'league__name')
    inlines = [StreamSourceInline, ScoreEventInline]
    readonly_fields = ('created_at', 'updated_at')

    def get_score(self, obj):
        if obj.score_summary:
            return f"{obj.score_summary.get('home', 0)} - {obj.score_summary.get('away', 0)}"
        return '-'
    get_score.short_description = 'Score'

    def stream_count(self, obj):
        count = obj.stream_sources.filter(is_active=True).count()
        return format_html('<span style="color: {};">{}</span>',
                           'green' if count > 0 else 'red', count)
    stream_count.short_description = 'Live Streams'


@admin.register(StreamSource)
class StreamSourceAdmin(admin.ModelAdmin):
    list_display = ('match', 'provider', 'priority', 'is_active', 'requires_auth', 'created_at')
    list_filter = ('provider', 'is_active', 'requires_auth')
    search_fields = ('match__home_team__name', 'match__away_team__name', 'url')
    readonly_fields = ('created_at',)


@admin.register(ScoreEvent)
class ScoreEventAdmin(admin.ModelAdmin):
    list_display = ('match', 'event_type', 'period', 'timestamp')
    list_filter = ('event_type',)
    search_fields = ('match__home_team__name', 'match__away_team__name')
    readonly_fields = ('created_at',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_at', 'created_at')
    list_filter = ('status', 'author')
    search_fields = ('title', 'body', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')


class AdCreativeInline(admin.TabularInline):
    model = AdCreative
    extra = 1
    fields = ('name', 'is_active', 'start_at', 'end_at')


@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ('label', 'slot_key', 'device_target', 'is_active', 'creative_count')
    list_filter = ('device_target', 'is_active')
    search_fields = ('label', 'slot_key')
    inlines = [AdCreativeInline]

    def creative_count(self, obj):
        return obj.creatives.filter(is_active=True).count()
    creative_count.short_description = 'Active Creatives'


@admin.register(AdCreative)
class AdCreativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'placement', 'is_active', 'start_at', 'end_at')
    list_filter = ('placement', 'is_active')
    search_fields = ('name',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'object_type', 'object_id', 'ip_address', 'timestamp')
    list_filter = ('action', 'object_type', 'timestamp')
    search_fields = ('actor__username', 'action', 'object_type', 'object_id')
    readonly_fields = ('actor', 'action', 'object_type', 'object_id',
                       'before_data', 'after_data', 'ip_address', 'user_agent', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
