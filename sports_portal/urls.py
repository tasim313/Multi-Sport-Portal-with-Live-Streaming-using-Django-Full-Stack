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
    live_matches, upcoming_matches, standings, get_ads, create_score_event,
    search, register_user, user_profile, index
)

# API Router
router = DefaultRouter()
router.register(r'sports', SportViewSet)
router.register(r'leagues', LeagueViewSet, basename='league')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Wagtail CMS Admin
    path('cms-admin/', include(wagtailadmin_urls)),

    # Wagtail documents
    path('documents/', include(wagtaildocs_urls)),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/live-matches/', live_matches, name='live-matches'),
    path('api/upcoming-matches/', upcoming_matches, name='upcoming-matches'),
    path('api/standings/', standings, name='standings'),
    path('api/ads/', get_ads, name='get-ads'),
    path('api/matches/<int:match_id>/events/', create_score_event, name='create-score-event'),

    # JWT Auth + User
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', register_user, name='register'),
    path('api/auth/profile/', user_profile, name='profile'),
    path('api/auth/', include('rest_framework.urls')),

    # Search
    path('api/search/', search, name='search'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Wagtail CMS pages
    path('cms/', include(wagtail_urls)),

    # React frontend - catch-all
    re_path(r'^(?!api/|django-admin/|cms-admin/|cms/|documents/|static/|media/).*$',
            index, name='frontend'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
