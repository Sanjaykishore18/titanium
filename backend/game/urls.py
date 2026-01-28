# ============================================================================
# COMPLETE urls.py
# Copy this ENTIRE file to: game/urls.py
# ============================================================================

from django.urls import path
from . import views

urlpatterns = [
    # ============= AUTHENTICATION =============
    path('', views.join_team_view, name='join_team_auth'),
    path('logout/', views.logout_view, name='logout'),
    
    # ============= TEAM DASHBOARD =============
    path('dashboard/', views.team_dashboard, name='team_dashboard'),
    
    # ============= ADMIN PANEL =============
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/create-team/', views.admin_create_team, name='admin_create_team'),
    path('admin-panel/teams/', views.admin_teams, name='admin_teams'),
    path('admin-panel/teams/<int:team_id>/', views.admin_team_detail, name='admin_team_detail'),
    path('admin-panel/round/<int:round_number>/control/', views.admin_round_control, name='admin_round_control'),
    path('admin-panel/leaderboard/', views.admin_leaderboard, name='admin_leaderboard'),
    
    # ============= API ENDPOINTS FOR FRONTEND =============
    path('api/start-game/', views.api_start_game, name='api_start_game'),
    path('api/validate-page/', views.api_validate_page, name='api_validate_page'),
    path('api/game-state/', views.api_get_game_state, name='api_game_state'),
]