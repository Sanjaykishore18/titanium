from django.contrib import admin
from .models import *

from django.contrib import admin
from django.contrib.auth.models import Group

# Remove Group model from admin
admin.site.unregister(Group)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'member_count', 'total_score_calculated','team_password', 'created_at']
    search_fields = ['team_name']
    list_filter = ['created_at']
    readonly_fields = ['created_at', 'created_by']
    ordering = ['-created_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['username', 'team', 'email', 'joined_at']
    search_fields = ['username', 'email', 'team__team_name']
    list_filter = ['team', 'joined_at']
    list_select_related = ['team', 'user']
    ordering = ['-joined_at']


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
        'pages_completed'
    ]
    list_filter = ['round', 'status', 'is_qualified']
    search_fields = ['team__team_name']
    list_editable = ['status', 'is_qualified']
    list_select_related = ['team', 'round']
    ordering = ['round__round_number', '-score']


@admin.register(PageProgress)
class PageProgressAdmin(admin.ModelAdmin):
    list_display = ['team_round', 'page_number', 'completed', 'time_taken_seconds']
    list_filter = ['completed', 'team_round__round']
    search_fields = ['team_round__team__team_name']
    list_select_related = ['team_round']
    ordering = ['team_round', 'page_number']


@admin.register(GameActivity)
class GameActivityAdmin(admin.ModelAdmin):
    list_display = ['team', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['team__team_name', 'description']
    date_hierarchy = 'timestamp'
    list_select_related = ['team']
    ordering = ['-timestamp']
