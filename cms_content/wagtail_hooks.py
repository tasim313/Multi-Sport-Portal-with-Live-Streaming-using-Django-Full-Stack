from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from wagtail import hooks
from wagtail.admin import messages
from django.urls import reverse
from django.utils.html import format_html
from django.templatetags.static import static

from sports.models import Sport, League, Team, Match, StreamSource, Article
from .models import Advertisement, SiteSettings

# Custom CSS and JS for admin
@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html(
        '<link rel="stylesheet" type="text/css" href="{}">',
        static('css/custom_admin.css')
    )

@hooks.register('insert_global_admin_js')
def global_admin_js():
    return format_html(
        '<script src="{}"></script>',
        static('js/custom_admin.js')
    )

# Sports Management in Wagtail Admin
class SportAdmin(ModelAdmin):
    model = Sport
    menu_label = 'Sports'
    menu_icon = 'pick'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'slug', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')

class LeagueAdmin(ModelAdmin):
    model = League
    menu_label = 'Leagues'
    menu_icon = 'list-ol'
    menu_order = 201
    list_display = ('name', 'sport', 'season', 'country', 'is_active')
    list_filter = ('sport', 'is_active', 'country')
    search_fields = ('name', 'season')

class TeamAdmin(ModelAdmin):
    model = Team
    menu_label = 'Teams'
    menu_icon = 'group'
    menu_order = 202
    list_display = ('name', 'short_name', 'league', 'country', 'is_active')
    list_filter = ('league__sport', 'league', 'is_active', 'country')
    search_fields = ('name', 'short_name')

class MatchAdmin(ModelAdmin):
    model = Match
    menu_label = 'Matches'
    menu_icon = 'date'
    menu_order = 203
    list_display = ('get_match_title', 'league', 'start_time', 'status', 'get_score')
    list_filter = ('status', 'league__sport', 'league', 'start_time')
    search_fields = ('home_team__name', 'away_team__name')
    
    def get_match_title(self, obj):
        return f"{obj.home_team.short_name} vs {obj.away_team.short_name}"
    get_match_title.short_description = 'Match'
    
    def get_score(self, obj):
        if obj.score_summary:
            return f"{obj.score_summary.get('home', 0)} - {obj.score_summary.get('away', 0)}"
        return "-"
    get_score.short_description = 'Score'

class StreamSourceAdmin(ModelAdmin):
    model = StreamSource
    menu_label = 'Live Streams'
    menu_icon = 'media'
    menu_order = 204
    list_display = ('match', 'provider', 'is_active', 'priority', 'requires_auth')
    list_filter = ('provider', 'is_active', 'requires_auth')
    search_fields = ('match__home_team__name', 'match__away_team__name')

class ArticleAdmin(ModelAdmin):
    model = Article
    menu_label = 'News Articles'
    menu_icon = 'doc-full'
    menu_order = 205
    list_display = ('title', 'author', 'status', 'published_at')
    list_filter = ('status', 'published_at', 'author')
    search_fields = ('title', 'body')

# Group sports-related models
class SportsGroup(ModelAdminGroup):
    menu_label = 'Sports Management'
    menu_icon = 'pick'
    menu_order = 200
    items = (SportAdmin, LeagueAdmin, TeamAdmin, MatchAdmin, StreamSourceAdmin, ArticleAdmin)

# Content Management
class AdvertisementAdmin(ModelAdmin):
    model = Advertisement
    menu_label = 'Advertisements'
    menu_icon = 'image'
    menu_order = 300
    list_display = ('name', 'placement', 'is_active', 'start_date', 'end_date')
    list_filter = ('placement', 'is_active')
    search_fields = ('name',)

class SiteSettingsAdmin(ModelAdmin):
    model = SiteSettings
    menu_label = 'Site Settings'
    menu_icon = 'cog'
    menu_order = 301
    list_display = ('site_name',)

class ContentGroup(ModelAdminGroup):
    menu_label = 'Content Management'
    menu_icon = 'folder-open-inverse'
    menu_order = 300
    items = (AdvertisementAdmin, SiteSettingsAdmin)

# Register model admin groups
modeladmin_register(SportsGroup)
modeladmin_register(ContentGroup)

# Custom dashboard panels
@hooks.register('construct_homepage_panels')
def add_custom_panels(request, panels):
    from django.template.loader import render_to_string
    
    panels.append({
        'order': 100,
        'html': render_to_string('wagtailadmin/custom_dashboard_panel.html', {
            'request': request,
        })
    })

# Custom branding - Hide Wagtail identity
@hooks.register('insert_global_admin_css')
def custom_branding():
    return """
    <style>
        /* Custom Sports Portal branding */
        .header {
            background: linear-gradient(135deg, #0B6E4F 0%, #1E293B 100%) !important;
        }
        
        .header-link {
            color: #F59E0B !important;
            font-weight: bold;
        }
        
        /* Hide Wagtail branding completely */
        .wagtail-logo, 
        .wagtail-logo-link,
        .wagtail-userbar-logo {
            display: none !important;
        }
        
        /* Custom logo replacement */
        .header .nav-wrapper::before {
            content: "🏆 Sports Portal CMS";
            color: #F59E0B;
            font-size: 20px;
            font-weight: bold;
            margin-right: 20px;
            display: inline-block;
        }
        
        /* Custom colors for buttons */
        .button, .button-secondary {
            background-color: #0B6E4F !important;
            border-color: #0B6E4F !important;
        }
        
        .button:hover, .button-secondary:hover {
            background-color: #064e38 !important;
        }
        
        /* Navigation styling */
        .nav-main a:hover {
            background-color: rgba(245, 158, 11, 0.1) !important;
        }
        
        /* Success messages */
        .messages .success {
            background-color: #0B6E4F !important;
        }
        
        /* Hide "View live" and "View draft" that might reveal it's Wagtail */
        .action-preview,
        .action-view-draft {
            display: none !important;
        }
        
        /* Custom page title */
        .breadcrumb {
            display: none;
        }
        
        /* Replace Wagtail references in help text */
        .help-block:contains("Wagtail") {
            display: none;
        }
    </style>
    """

# Remove Wagtail help links
@hooks.register('construct_main_menu')
def hide_wagtail_help(request, menu_items):
    # Remove help menu item that might reveal Wagtail
    menu_items[:] = [item for item in menu_items if getattr(item, 'name', '') != 'help']

# Custom welcome message
@hooks.register('construct_homepage_summary_items')
def add_custom_summary_items(request, summary_items):
    summary_items.clear()  # Remove default Wagtail summary
    
    # Add custom summary items
    from sports.models import Match
    from django.utils import timezone
    
    live_matches = Match.objects.filter(status='live').count()
    upcoming_matches = Match.objects.filter(
        status='scheduled',
        start_time__gt=timezone.now()
    ).count()
    
    summary_items.append({
        'icon': 'media',
        'text': f'{live_matches} Live Matches',
        'description': 'Currently broadcasting',
        'url': '/cms-admin/sports/match/',
    })
    
    summary_items.append({
        'icon': 'date',
        'text': f'{upcoming_matches} Upcoming Matches',
        'description': 'Scheduled for broadcast',
        'url': '/cms-admin/sports/match/',
    })