# ============================================================================
# COMPLETE CORRECTED models.py with SIGNAL HANDLERS
# Copy this ENTIRE file to: game/models.py
# ============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

class Team(models.Model):
    team_name = models.CharField(max_length=100, unique=True)
    team_password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    
    def __str__(self):
        return self.team_name
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def total_score_calculated(self):
        """Calculate total score from all round progress"""
        total = self.round_progress.aggregate(total=Sum('score'))['total']
        return total if total else 0


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_membership')
    username = models.CharField(max_length=100)
    email = models.EmailField()
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['team', 'user']
    
    def __str__(self):
        return f"{self.username} - {self.team.team_name}"


class Round(models.Model):
    ROUND_CHOICES = [
        (1, 'Round 1 - Stranger Things'),
        (2, 'Round 2 - One Piece'),
        (3, 'Round 3 - Squid Game'),
    ]
    
    round_number = models.IntegerField(choices=ROUND_CHOICES, unique=True)
    is_open = models.BooleanField(default=False)
    duration_minutes = models.IntegerField(default=60)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Round {self.round_number}"
    
    @property
    def is_active(self):
        """Check if round is currently active"""
        if not self.is_open:
            return False
        if not self.start_time:
            return False
        now = timezone.now()
        if self.end_time and now > self.end_time:
            return False
        return now >= self.start_time


class TeamRoundProgress(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('time_over', 'Time Over'),
        ('qualified', 'Qualified'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='round_progress')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='team_progress')
    current_page = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    is_qualified = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['team', 'round']
        ordering = ['round__round_number']
    
    def __str__(self):
        return f"{self.team.team_name} - Round {self.round.round_number}"
    
    @property
    def pages_completed(self):
        return self.page_progress.filter(completed=True).count()


class PageProgress(models.Model):
    team_round = models.ForeignKey(TeamRoundProgress, on_delete=models.CASCADE, related_name='page_progress')
    page_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    bugs_fixed = models.JSONField(default=list)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['team_round', 'page_number']
        ordering = ['page_number']
    
    def __str__(self):
        return f"{self.team_round.team.team_name} - R{self.team_round.round.round_number} Page {self.page_number}"


class GameActivity(models.Model):
    ACTIVITY_TYPES = [
        ('team_created', 'Team Created'),
        ('member_joined', 'Member Joined'),
        ('round_started', 'Round Started'),
        ('page_completed', 'Page Completed'),
        ('round_completed', 'Round Completed'),
        ('bug_fixed', 'Bug Fixed'),
        ('time_over', 'Time Over'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Game Activities'
    
    def __str__(self):
        return f"{self.team.team_name} - {self.activity_type}"


# ============================================================================
# SIGNAL HANDLERS - Ensures score consistency when admin deletes progress
# ============================================================================

@receiver(post_delete, sender=TeamRoundProgress)
def handle_round_progress_deletion(sender, instance, **kwargs):
    """
    When admin deletes TeamRoundProgress, this ensures:
    1. Team's total score is automatically recalculated
    2. Related activities are logged
    """
    team = instance.team
    
    # Log the deletion activity
    GameActivity.objects.create(
        team=team,
        activity_type='round_completed',  # Reusing existing type
        description=f'Round {instance.round.round_number} progress was reset by admin',
        metadata={
            'previous_score': instance.score,
            'round_number': instance.round.round_number,
            'admin_action': True
        }
    )
    
    # Note: total_score_calculated is a property that auto-calculates,
    # so no manual update needed - it will reflect correctly on next access


@receiver(post_delete, sender=PageProgress)
def handle_page_progress_deletion(sender, instance, **kwargs):
    """
    When admin deletes PageProgress, recalculate the parent round's score
    """
    team_round = instance.team_round
    
    # Recalculate score based on remaining completed pages
    completed_pages = team_round.page_progress.filter(completed=True).count()
    team_round.score = completed_pages * 10  # 10 points per page
    team_round.save(update_fields=['score'])


@receiver(post_save, sender=TeamRoundProgress)
def update_team_activity_on_progress_change(sender, instance, created, **kwargs):
    """
    Log activity when progress is updated (optional, for better tracking)
    """
    if not created and instance.status == 'not_started':
        # If status was reset to not_started, it might be an admin reset
        # Note: This only fires if the record was updated, not deleted
        pass