# ============================================================================
# UPDATED urls.py with Static Files Serving
# Replace: escape_game_project/urls.py
# ============================================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game.urls')),
]

# ✅ CRITICAL: Serve static files in development
# This is what was missing!
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)