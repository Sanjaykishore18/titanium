"""
Django settings for escape_game_project project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ss881e0icnut0^z%ptbu8n4gvk%)l@az4r8)1=f_zg!x5)v4fh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ✅ UPDATED: New IP address
ALLOWED_HOSTS = [
    "10.98.207.227",
    "localhost",
    "127.0.0.1",
    ".trycloudflare.com",
]

# ✅ FIX: Remove Cross-Origin-Opener-Policy header
SECURE_CROSS_ORIGIN_OPENER_POLICY = None


# Application definition
INSTALLED_APPS = [
    "jazzmin",  # Must be FIRST for admin styling
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  # ✅ CRITICAL for static files
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'corsheaders',
    'game',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'escape_game_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'escape_game_project.wsgi.application'
ASGI_APPLICATION = 'escape_game_project.asgi.application'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ============================================================================
# CHANNELS & WEBSOCKET CONFIGURATION
# ============================================================================
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}


# ============================================================================
# STATIC FILES CONFIGURATION - ✅ COMPLETE FIX
# ============================================================================

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# ✅ Where collectstatic will copy all static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ✅ Additional directories to look for static files
STATICFILES_DIRS = []

# ✅ Static files finders (how Django finds your static files)
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ✅ CRITICAL: Storage backend for static files
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================================
# JAZZMIN ADMIN CONFIGURATION
# ============================================================================
JAZZMIN_SETTINGS = {
    "site_title": "Web Escape Admin",
    "site_header": "Web Escape",
    "site_brand": "Web Escape Game",
    "welcome_sign": "Welcome to Web Escape Admin",
    "copyright": "Web Escape Game 2026",
    
    "search_model": ["auth.User", "game.Team", "game.TeamMember"],
    "user_avatar": None,
    
    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Teams", "url": "admin:game_team_changelist", "permissions": ["game.view_team"]},
        {"name": "Rounds", "url": "admin:game_round_changelist", "permissions": ["game.view_round"]},
        {"model": "auth.User"},
    ],
    
    # User Menu
    "usermenu_links": [
        {"model": "auth.user"}
    ],
    
    # Side Menu
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["game", "auth"],
    
    # Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "game.Team": "fas fa-users",
        "game.TeamMember": "fas fa-user-friends",
        "game.Round": "fas fa-gamepad",
        "game.TeamRoundProgress": "fas fa-chart-line",
        "game.PageProgress": "fas fa-tasks",
        "game.GameActivity": "fas fa-history",
    },
    
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

# UI Customization for Dark Theme
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-purple",
    "navbar": "navbar-dark navbar-purple",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-purple",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "darkly",
    "dark_mode_theme": "darkly",
    "button_classes": {
        "primary": "btn-purple",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": False
}


# ============================================================================
# CRISPY FORMS
# ============================================================================
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ============================================================================
# AUTHENTICATION
# ============================================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'


# ============================================================================
# CORS CONFIGURATION
# ============================================================================
CORS_ALLOWED_ORIGINS = [
    "http://10.98.207.227:8080",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

CORS_ALLOW_CREDENTIALS = True

# ✅ CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    "http://10.98.207.227:8000",
    "http://10.98.207.227:8080",
    "http://localhost:8000",
    "http://localhost:8080",
]

# Frontend URL
FRONTEND_URL = 'http://10.98.207.227:8080'