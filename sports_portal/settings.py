import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config('SECRET_KEY', default='django-insecure-sports-portal-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,103.166.187.149', cast=lambda v: [s.strip() for s in v.split(',')])

# Application definition
DJANGO_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

WAGTAIL_APPS = [
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'wagtail.contrib.routable_page',
    'wagtail.contrib.styleguide',
    'modelcluster',
    'taggit',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'csp',
    'axes',
    'drf_spectacular',
    'django_extensions',
]

LOCAL_APPS = [
    'sports',
    'cms_content',
]

INSTALLED_APPS = DJANGO_APPS + WAGTAIL_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
]

ROOT_URLCONF = 'sports_portal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'frontend' / 'build',
            BASE_DIR / 'templates',
            BASE_DIR,
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sports_portal.wsgi.application'
ASGI_APPLICATION = 'sports_portal.asgi.application'

# Custom User Model
AUTH_USER_MODEL = 'sports.User'

# Database
if config('USE_SQLITE_FALLBACK', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='sports_portal'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Redis & Channels
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# JWT Auth URLs
SPECTACULAR_SETTINGS = {
    'TITLE': 'Multi-Sport Portal API',
    'DESCRIPTION': """
## Overview
REST API for the Multi-Sport Portal — supporting Cricket, Football, and Tennis with
live streaming, real-time score updates (WebSocket), news articles, ad management,
and role-based access control.

## Authentication
This API uses **JWT (Bearer token)** authentication.

1. Call `POST /api/auth/token/` with your username and password to get an access token.
2. Include the token in subsequent requests:
   ```
   Authorization: Bearer <access_token>
   ```
3. Access tokens expire after **60 minutes**. Use `POST /api/auth/token/refresh/` with
   your refresh token to get a new access token (refresh tokens last **7 days**).

## User Roles
| Role | Description |
|------|-------------|
| `anonymous` | Read-only access to public matches and articles |
| `registered` | Auth-required streams and profile management |
| `subscriber` | Premium content access |
| `editor` | Can create score events and articles |
| `streamer_admin` | Full match and stream management |
| `sysadmin` | Full system access |

## Real-Time Updates
Connect via WebSocket at `ws://<host>/ws/matches/<match_id>/` to receive live score
events (`score_update`) and match status changes (`match_status_update`) pushed
in real time without polling.

## Pagination
All list endpoints use page-number pagination. Default page size is **20**.
Use `?page=2` to navigate. Response includes `count`, `next`, and `previous`.
""",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'CONTACT': {
        'name': 'Sports Portal Team',
    },
    'LICENSE': {
        'name': 'MIT License',
    },
    'TAGS': [
        {'name': 'sports', 'description': 'Sport categories (Cricket, Football, Tennis)'},
        {'name': 'leagues', 'description': 'Leagues and tournaments within a sport'},
        {'name': 'teams', 'description': 'Teams and clubs'},
        {'name': 'matches', 'description': 'Match scheduling, live status, streams, and score events'},
        {'name': 'articles', 'description': 'News articles published via CMS'},
        {'name': 'auth', 'description': 'JWT authentication, registration, and user profile'},
        {'name': 'ads', 'description': 'Ad placement and creative retrieval'},
        {'name': 'search', 'description': 'Global search across matches, articles, and teams'},
    ],
    'POSTPROCESSING_HOOKS': ['drf_spectacular.hooks.postprocess_schema_enums'],
    'DISABLE_ERRORS_AND_WARNINGS': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}

# CORS Settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# CSP Settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://www.youtube.com", "https://player.vimeo.com")
CSP_FRAME_SRC = ("'self'", "https://www.youtube.com", "https://player.vimeo.com", "https://www.youtube-nocookie.com")
CSP_IMG_SRC = ("'self'", "data:", "https:", "http:")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "ws:", "wss:", "https:", "http:")
CSP_MEDIA_SRC = ("'self'", "https:", "http:", "blob:")

# Security Settings (always on)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # SAMEORIGIN needed for Wagtail admin iframes

# Silence system check warnings that are intentional or handled at deploy time
SILENCED_SYSTEM_CHECKS = [
    'security.W019',  # X_FRAME_OPTIONS SAMEORIGIN — intentional for Wagtail admin iframes
    'drf_spectacular.W001',  # Wagtail admin operationId collisions — third-party, unfixable
    'drf_spectacular.W002',  # Wagtail admin serializer errors — third-party, unfixable
]

# Production-only security settings (activated when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Axes (brute force protection)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = ['ip_address']

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Add Vite build output if it exists
_vite_build = BASE_DIR / 'frontend' / 'build' / 'static'
if _vite_build.exists():
    STATICFILES_DIRS.append(_vite_build)

_vite_public_build = BASE_DIR / 'frontend' / 'build'
if _vite_public_build.exists():
    STATICFILES_DIRS.append(_vite_public_build)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Wagtail settings
WAGTAIL_SITE_NAME = 'Sports Portal CMS'
WAGTAIL_ADMIN_URL = 'cms-admin'
WAGTAILADMIN_BASE_URL = config('WAGTAIL_BASE_URL', default='http://localhost:8000')
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': str(BASE_DIR / 'sports_portal.log'),
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'sports': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'auto-start-matches': {
        'task': 'sports.tasks.auto_start_matches',
        'schedule': 60.0,  # every 60 seconds
    },
    'auto-finish-matches': {
        'task': 'sports.tasks.auto_finish_matches',
        'schedule': 60.0,
    },
    'cleanup-audit-logs': {
        'task': 'sports.tasks.cleanup_old_audit_logs',
        'schedule': crontab(hour=2, minute=0),  # daily at 2am
    },
}
