# ============================================================================
# FINAL admin.py - CSV Export + Leaderboard Buttons for Django Admin
# Copy this to: game/admin.py
# ============================================================================

from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
import csv
from .models import *

# Remove Group model from admin
admin.site.unregister(Group)


# ============================================================================
# CSV EXPORT ACTION
# ============================================================================

def export_to_csv(modeladmin, request, queryset):
    """Export selected Team Round Progress to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="team_round_progress.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Team ID', 'Team Name', 'Round Number', 'Round Name',
        'Current Page', 'Score', 'Status', 'Is Qualified',
        'Pages Completed', 'Start Time', 'End Time', 'Duration (seconds)', 'Is Active'
    ])
    
    round_names = {
        1: 'Round 1 - Stranger Things',
        2: 'Round 2 - One Piece',
        3: 'Round 3 - Squid Game'
    }
    
    for progress in queryset.select_related('team', 'round'):
        writer.writerow([
            progress.team.id,
            progress.team.team_name,
            progress.round.round_number,
            round_names.get(progress.round.round_number, f'Round {progress.round.round_number}'),
            progress.current_page,
            progress.score,
            progress.get_status_display(),
            'Yes' if progress.is_qualified else 'No',
            progress.pages_completed,
            progress.start_time.strftime('%Y-%m-%d %H:%M:%S') if progress.start_time else 'Not Started',
            progress.end_time.strftime('%Y-%m-%d %H:%M:%S') if progress.end_time else 'In Progress',
            progress.duration_seconds,
            'Yes' if progress.is_active else 'No'
        ])
    
    return response

export_to_csv.short_description = "📥 Export selected to CSV"


def export_all_to_csv(modeladmin, request, queryset):
    """Export ALL Team Round Progress to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="all_team_round_progress.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Team ID', 'Team Name', 'Round Number', 'Round Name',
        'Current Page', 'Score', 'Status', 'Is Qualified',
        'Pages Completed', 'Start Time', 'End Time', 'Duration (seconds)', 'Is Active'
    ])
    
    round_names = {
        1: 'Round 1 - Stranger Things',
        2: 'Round 2 - One Piece',
        3: 'Round 3 - Squid Game'
    }
    
    all_progress = TeamRoundProgress.objects.select_related('team', 'round').order_by('team__team_name', 'round__round_number')
    
    for progress in all_progress:
        writer.writerow([
            progress.team.id,
            progress.team.team_name,
            progress.round.round_number,
            round_names.get(progress.round.round_number, f'Round {progress.round.round_number}'),
            progress.current_page,
            progress.score,
            progress.get_status_display(),
            'Yes' if progress.is_qualified else 'No',
            progress.pages_completed,
            progress.start_time.strftime('%Y-%m-%d %H:%M:%S') if progress.start_time else 'Not Started',
            progress.end_time.strftime('%Y-%m-%d %H:%M:%S') if progress.end_time else 'In Progress',
            progress.duration_seconds,
            'Yes' if progress.is_active else 'No'
        ])
    
    return response

export_all_to_csv.short_description = "📥 Export ALL to CSV"


# ============================================================================
# TEAM ADMIN
# ============================================================================

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'member_count', 'total_score_calculated', 'team_password', 'created_at']
    search_fields = ['team_name']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'created_by']
    ordering = ['-created_at']

    def save_model(self, request, obj, form, change):
        """Automatically set `created_by` to the current user when creating a Team in admin."""
        if not change and not getattr(obj, 'created_by', None):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================================
# TEAM MEMBER ADMIN
# ============================================================================

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['username', 'team', 'email', 'joined_at']
    search_fields = ['username', 'email', 'team__team_name']
    list_filter = ['team', 'joined_at']
    list_select_related = ['team', 'user']
    ordering = ['-joined_at']


# ============================================================================
# ROUND ADMIN
# ============================================================================

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'round_number',
        'is_open',
        'duration_minutes',
        'start_time',
        'end_time',
        'is_active_display',
    )

    list_filter = ['is_open', 'round_number']
    list_editable = ['is_open', 'duration_minutes']
    ordering = ['round_number']

    def is_active_display(self, obj):
        return obj.is_active

    is_active_display.boolean = True
    is_active_display.short_description = "Is Active"


# ============================================================================
# TEAM ROUND PROGRESS ADMIN - WITH CSV + LEADERBOARD BUTTONS
# ============================================================================

@admin.register(TeamRoundProgress)
class TeamRoundProgressAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'team',
        'round',
        'current_page',
        'score',
        'status',
        'is_qualified',
        'pages_completed',
        'quick_actions'  # ⭐ BUTTONS COLUMN ⭐
    ]
    list_filter = ['round', 'status', 'is_qualified']
    search_fields = ['team__team_name']
    list_editable = ['status', 'is_qualified']
    list_select_related = ['team', 'round']
    ordering = ['round__round_number', '-score']
    
    # ⭐ CSV EXPORT ACTIONS ⭐
    actions = [export_to_csv, export_all_to_csv]
    
    # ⭐ BUTTONS IN EACH ROW ⭐
    def quick_actions(self, obj):
        """CSV and Leaderboard buttons"""
        csv_url = reverse('export_team_round_progress')
        leaderboard_url = reverse('public_leaderboard')
        
        return format_html(
            '<a href="{}" style="display:inline-block;background:#28a745;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;margin-right:5px;font-size:11px;">📥 CSV</a>'
            '<a href="{}" target="_blank" style="display:inline-block;background:#ffc107;color:#000;padding:5px 10px;border-radius:4px;text-decoration:none;font-size:11px;">🏆 Board</a>',
            csv_url,
            leaderboard_url
        )
    
    quick_actions.short_description = 'Quick Actions'


# ============================================================================
# PAGE PROGRESS ADMIN
# ============================================================================

@admin.register(PageProgress)
class PageProgressAdmin(admin.ModelAdmin):
    list_display = ['team_round', 'page_number', 'completed', 'time_taken_seconds']
    list_filter = ['completed', 'team_round__round']
    search_fields = ['team_round__team__team_name']
    list_select_related = ['team_round']
    ordering = ['team_round', 'page_number']


# ============================================================================
# GAME ACTIVITY ADMIN
# ============================================================================

@admin.register(GameActivity)
class GameActivityAdmin(admin.ModelAdmin):
    list_display = ['team', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['team__team_name', 'description']
    date_hierarchy = 'timestamp'
    list_select_related = ['team']
    ordering = ['-timestamp']


# ============================================================================
# ADMIN SITE CONFIGURATION
# ============================================================================

admin.site.site_header = "Web Escape Game Admin"
admin.site.site_title = "Game Admin Portal"
admin.site.index_title = "Welcome to Game Administration"