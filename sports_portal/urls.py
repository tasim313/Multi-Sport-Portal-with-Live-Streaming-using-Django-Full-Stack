from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from sports.views import (
    SportViewSet, LeagueViewSet, TeamViewSet, MatchViewSet, ArticleViewSet,
    IPTVChannelViewSet, PlayerProfileViewSet, LeagueTableViewSet,
    live_matches, upcoming_matches, standings, get_ads, create_score_event,
    add_commentary, search, register_user, user_profile,
    list_favorites, add_favorite, remove_favorite,
    trigger_iptv_import, index
)

# API Router
router = DefaultRouter()
router.register(r'sports', SportViewSet)
router.register(r'leagues', LeagueViewSet, basename='league')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'players', PlayerProfileViewSet, basename='player')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'iptv/channels', IPTVChannelViewSet, basename='iptv-channel')
router.register(r'standings', LeagueTableViewSet, basename='standings-table')

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Wagtail CMS Admin
    path('cms-admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),

    # API endpoints
    path('api/', include(router.urls)),

    # Match actions
    path('api/live-matches/', live_matches, name='live-matches'),
    path('api/upcoming-matches/', upcoming_matches, name='upcoming-matches'),
    path('api/standings/', standings, name='standings'),
    path('api/matches/<int:match_id>/events/', create_score_event, name='create-score-event'),
    path('api/matches/<int:match_id>/commentary/', add_commentary, name='add-commentary'),

    # Ads
    path('api/ads/', get_ads, name='get-ads'),

    # JWT Auth + User
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', register_user, name='register'),
    path('api/auth/profile/', user_profile, name='profile'),
    path('api/auth/', include('rest_framework.urls')),

    # User favorites
    path('api/favorites/', list_favorites, name='list-favorites'),
    path('api/favorites/add/', add_favorite, name='add-favorite'),
    path('api/favorites/<str:item_type>/<int:item_id>/', remove_favorite, name='remove-favorite'),

    # Search
    path('api/search/', search, name='search'),

    # IPTV admin trigger
    path('api/iptv/import/', trigger_iptv_import, name='trigger-iptv-import'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Wagtail CMS pages
    path('cms/', include(wagtail_urls)),

    # React/Next.js frontend — catch-all
    re_path(r'^(?!api/|django-admin/|cms-admin/|cms/|documents/|static/|media/).*$',
            index, name='frontend'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
