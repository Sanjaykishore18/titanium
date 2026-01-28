# ============================================================================
# COMPLETE CORRECTED views.py with IMPROVED LOGIC
# Copy this ENTIRE file to: game/views.py
# ============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Case, When, IntegerField
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import hashlib
import json
from .models import *

# ============= HELPER FUNCTIONS =============

def is_superuser(user):
    return user.is_superuser

def get_user_team(user):
    try:
        return user.team_membership.team
    except:
        return None

def generate_page_token(team_id, round_num, page_num, secret_key):
    '''Generate secure token for page access'''
    data = f"{team_id}-{round_num}-{page_num}-{secret_key}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

# ============= AUTHENTICATION VIEWS =============

def join_team_view(request):
    if request.user.is_authenticated:
        team = get_user_team(request.user)
        if team:
            return redirect('team_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        team_password = request.POST.get('team_password')
        
        try:
            team = Team.objects.get(team_password=team_password)
        except Team.DoesNotExist:
            messages.error(request, 'Invalid team password')
            return render(request, 'join_team_auth.html')
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        
        if not created and hasattr(user, 'team_membership'):
            messages.warning(request, 'You are already part of a team')
            login(request, user)
            return redirect('team_dashboard')
        
        TeamMember.objects.create(
            team=team,
            user=user,
            username=username,
            email=email
        )
        
        GameActivity.objects.create(
            team=team,
            activity_type='member_joined',
            description=f'{username} joined the team'
        )
        
        login(request, user)
        messages.success(request, f'Welcome to {team.team_name}!')
        return redirect('team_dashboard')
    
    return render(request, 'join_team_auth.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('join_team_auth')

# ============= TEAM DASHBOARD (IMPROVED) =============

@login_required
def team_dashboard(request):
    team = get_user_team(request.user)
    if not team:
        messages.error(request, 'You are not part of any team')
        return redirect('join_team_auth')
    
    # Get all rounds
    rounds = Round.objects.all().order_by('round_number')
    
    # Create/get progress for each round with proper defaults
    round_progress_list = []
    rounds_completed = 0
    
    for round_obj in rounds:
        progress, created = TeamRoundProgress.objects.get_or_create(
            team=team,
            round=round_obj,
            defaults={'status': 'not_started', 'score': 0}
        )
        
        # Recalculate score based on actual completed pages (fixes admin deletion issue)
        if progress.status != 'not_started':
            completed_pages = progress.page_progress.filter(completed=True).count()
            calculated_score = completed_pages * 10
            
            # Update if score doesn't match (e.g., after admin deleted pages)
            if progress.score != calculated_score:
                progress.score = calculated_score
                progress.save(update_fields=['score'])
        
        round_progress_list.append(progress)
        
        if progress.status in ['completed', 'qualified']:
            rounds_completed += 1
    
    # Zip rounds and progress together for template
    rounds_with_progress = list(zip(rounds, round_progress_list))
    
    # Get leaderboard with optimized query and accurate calculations
    all_teams = Team.objects.annotate(
        total_score=Sum('round_progress__score'),
        members_count=Count('members', distinct=True),
        rounds_completed=Count(
            Case(
                When(
                    round_progress__status__in=['completed', 'qualified'],
                    then=1
                ),
                output_field=IntegerField()
            )
        )
    ).order_by('-total_score', 'created_at')
    
    # Calculate current team's rank
    team_rank = 1
    for idx, t in enumerate(all_teams, 1):
        if t.id == team.id:
            team_rank = idx
            break
    
    # Get top 15 teams for leaderboard
    top_teams = all_teams[:15]
    
    # Calculate total score (using property for consistency)
    total_score = team.total_score_calculated
    
    context = {
        'team': team,
        'rounds_with_progress': rounds_with_progress,
        'rounds_completed': rounds_completed,
        'team_rank': team_rank,
        'total_teams': all_teams.count(),
        'top_teams': top_teams,
        'total_score': total_score,
    }
    
    return render(request, 'team_dashboard.html', context)

# ============= ADMIN VIEWS =============

@user_passes_test(is_superuser)
def admin_dashboard(request):
    total_teams = Team.objects.count()
    total_participants = TeamMember.objects.count()
    
    rounds = Round.objects.all().order_by('round_number')
    
    teams = Team.objects.annotate(
        total_score=Sum('round_progress__score'),
        pages_completed=Count('round_progress__page_progress', filter=Q(round_progress__page_progress__completed=True))
    ).order_by('-total_score', 'created_at')
    
    round_stats = {}
    for round_obj in rounds:
        stats = TeamRoundProgress.objects.filter(round=round_obj).aggregate(
            teams_started=Count('id', filter=Q(status__in=['in_progress', 'completed', 'time_over', 'qualified'])),
            teams_completed=Count('id', filter=Q(status__in=['completed', 'qualified'])),
            avg_score=Sum('score')
        )
        round_stats[round_obj.round_number] = stats
    
    context = {
        'total_teams': total_teams,
        'total_participants': total_participants,
        'rounds': rounds,
        'teams': teams[:20],
        'round_stats': round_stats,
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(is_superuser)
def admin_create_team(request):
    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        team_password = request.POST.get('team_password')
        
        if Team.objects.filter(team_name=team_name).exists():
            messages.error(request, 'Team name already exists')
        else:
            Team.objects.create(
                team_name=team_name,
                team_password=team_password,
                created_by=request.user
            )
            messages.success(request, f'Team "{team_name}" created successfully!')
            return redirect('admin_teams')
    
    return render(request, 'admin_create_team.html')

@user_passes_test(is_superuser)
def admin_teams(request):
    teams = Team.objects.annotate(
        member_count=Count('members'),
        total_score=Sum('round_progress__score')
    ).order_by('-created_at')
    
    context = {'teams': teams}
    return render(request, 'admin_teams.html', context)

@user_passes_test(is_superuser)
def admin_team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    members = team.members.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_member':
            username = request.POST.get('username')
            email = request.POST.get('email')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            
            TeamMember.objects.get_or_create(
                team=team,
                user=user,
                defaults={'username': username, 'email': email}
            )
            messages.success(request, f'Added {username} to team')
        
        elif action == 'remove_member':
            member_id = request.POST.get('member_id')
            TeamMember.objects.filter(id=member_id).delete()
            messages.success(request, 'Member removed')
        
        return redirect('admin_team_detail', team_id=team_id)
    
    context = {'team': team, 'members': members}
    return render(request, 'admin_team_detail.html', context)

@user_passes_test(is_superuser)
def admin_round_control(request, round_number):
    round_obj = get_object_or_404(Round, round_number=round_number)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'open_round':
            round_obj.is_open = True
            round_obj.start_time = timezone.now()
            round_obj.save()
            messages.success(request, f'Round {round_number} is now open for all teams!')
        
        elif action == 'close_round':
            round_obj.is_open = False
            round_obj.save()
            messages.success(request, f'Round {round_number} is now closed')
        
        elif action == 'set_duration':
            duration = int(request.POST.get('duration', 60))
            round_obj.duration_minutes = duration
            round_obj.save()
            messages.success(request, f'Duration set to {duration} minutes')
        
        elif action == 'qualify_all':
            TeamRoundProgress.objects.filter(
                round=round_obj,
                status='completed'
            ).update(is_qualified=True, status='qualified')
            messages.success(request, 'All completed teams qualified!')
        
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@user_passes_test(is_superuser)
def admin_leaderboard(request):
    teams = Team.objects.annotate(
        total_score=Sum('round_progress__score'),
        pages_completed=Count('round_progress__page_progress', filter=Q(round_progress__page_progress__completed=True))
    ).order_by('-total_score', 'created_at')
    
    rounds = Round.objects.all()
    round_leaderboards = {}
    for round_obj in rounds:
        round_teams = TeamRoundProgress.objects.filter(
            round=round_obj
        ).select_related('team').order_by('-score', 'duration_seconds')
        round_leaderboards[round_obj.round_number] = round_teams
    
    context = {
        'teams': teams,
        'rounds': rounds,
        'round_leaderboards': round_leaderboards,
    }
    return render(request, 'admin_leaderboard.html', context)

# ============= API ENDPOINTS FOR FRONTEND =============

@login_required
def api_start_game(request):
    '''API: Start game and get first page URL with token'''
    if request.method == 'POST':
        data = json.loads(request.body)
        round_number = data.get('round_number')
        
        team = get_user_team(request.user)
        if not team:
            return JsonResponse({'error': 'No team found'}, status=403)
        
        round_obj = get_object_or_404(Round, round_number=round_number)
        
        if not round_obj.is_open:
            return JsonResponse({'error': 'Round not open yet'}, status=403)
        
        # Get or create team round progress
        team_round, created = TeamRoundProgress.objects.get_or_create(
            team=team,
            round=round_obj,
            defaults={
                'status': 'in_progress',
                'is_active': True,
                'start_time': timezone.now(),
                'end_time': timezone.now() + timedelta(minutes=round_obj.duration_minutes),
                'score': 0,
                'current_page': 1
            }
        )
        
        # Determine page number
        is_new_start = created or team_round.status == 'not_started'
        current_page = 1
        
        if not is_new_start and team_round.status == 'in_progress':
            current_page = team_round.current_page or 1
        elif is_new_start:
            team_round.status = 'in_progress'
            team_round.is_active = True
            team_round.start_time = timezone.now()
            team_round.end_time = timezone.now() + timedelta(minutes=round_obj.duration_minutes)
            team_round.current_page = 1
            team_round.save()
            
            GameActivity.objects.create(
                team=team,
                activity_type='round_started',
                description=f'Started Round {round_number}'
            )
        
        from django.conf import settings
        token = generate_page_token(team.id, round_number, current_page, settings.SECRET_KEY)
        
        time_remaining = int((team_round.end_time - timezone.now()).total_seconds())
        
        # ✅ FIX: ADD current_page to URL parameters
        page_url = f"{settings.FRONTEND_URL}/round{round_number}/page{current_page}.html?token={token}&team={team.id}&round={round_number}&page={current_page}"
        
        return JsonResponse({
            'success': True,
            'page_url': page_url,  # ✅ Now includes page parameter
            'team_id': team.id,
            'round_number': round_number,
            'current_page': current_page,
            'token': token,
            'is_new_start': is_new_start,
            'time_remaining': max(0, time_remaining),
            'current_score': team_round.score
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def api_validate_page(request):
    '''API: Validate page completion and return next page URL'''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            token = data.get('token')
            round_number = data.get('round_number')
            page_number = data.get('page_number')
            bugs_fixed = data.get('bugs_fixed', [])
            team_id = data.get('team_id')
            
            from django.conf import settings
            expected_token = generate_page_token(team_id, round_number, page_number, settings.SECRET_KEY)
            
            if token != expected_token:
                return JsonResponse({
                    'error': 'Invalid token',
                    'details': 'Security token validation failed'
                }, status=403)
            
            team = get_object_or_404(Team, id=team_id)
            round_obj = get_object_or_404(Round, round_number=round_number)
            team_round = get_object_or_404(TeamRoundProgress, team=team, round=round_obj)
            
            # Check time
            if timezone.now() > team_round.end_time:
                team_round.status = 'time_over'
                team_round.is_active = False
                team_round.save()
                return JsonResponse({
                    'error': 'Time over',
                    'redirect_dashboard': True
                }, status=403)
            
            # Check bugs fixed
            if len(bugs_fixed) < 3:
                return JsonResponse({
                    'error': 'All 3 bugs must be fixed',
                    'bugs_required': 3,
                    'bugs_fixed': len(bugs_fixed)
                }, status=400)
            
            # Save page progress
            page_progress, created = PageProgress.objects.get_or_create(
                team_round=team_round,
                page_number=page_number
            )
            
            if not page_progress.completed:
                page_progress.completed = True
                page_progress.completed_at = timezone.now()
                page_progress.bugs_fixed = bugs_fixed
                page_progress.time_taken_seconds = int((page_progress.completed_at - page_progress.started_at).total_seconds())
                page_progress.save()
                
                # Add 10 points for completing the page
                team_round.score += 10
                team_round.current_page = page_number + 1
                team_round.save()
                
                GameActivity.objects.create(
                    team=team,
                    activity_type='page_completed',
                    description=f'Completed Round {round_number} Page {page_number}'
                )
            
            # Next page or completion
            if page_number < 10:
                next_page = page_number + 1
                next_token = generate_page_token(team_id, round_number, next_page, settings.SECRET_KEY)
                next_url = f"{settings.FRONTEND_URL}/round{round_number}/page{next_page}.html?token={next_token}&team={team_id}"
                
                return JsonResponse({
                    'success': True,
                    'next_page_url': next_url,
                    'current_score': team_round.score,
                    'pages_completed': page_number,
                    'total_pages': 10
                })
            else:
                # Round completed
                team_round.status = 'completed'
                team_round.is_active = False
                team_round.end_time = timezone.now()
                team_round.duration_seconds = int((team_round.end_time - team_round.start_time).total_seconds())
                team_round.save()
                
                GameActivity.objects.create(
                    team=team,
                    activity_type='round_completed',
                    description=f'Completed Round {round_number}',
                    metadata={'score': team_round.score}
                )
                
                return JsonResponse({
                    'success': True,
                    'round_completed': True,
                    'final_score': team_round.score,
                    'redirect_dashboard': True,
                    'message': f'Round {round_number} Completed!'
                })
        
        except Exception as e:
            print(f"ERROR in api_validate_page: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'error': 'Server error',
                'details': str(e)
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def api_get_game_state(request):
    '''API: Get current game state (score, time, etc.)'''
    if request.method == 'POST':
        data = json.loads(request.body)
        team_id = data.get('team_id')
        round_number = data.get('round_number')
        
        team = get_object_or_404(Team, id=team_id)
        round_obj = get_object_or_404(Round, round_number=round_number)
        team_round = get_object_or_404(TeamRoundProgress, team=team, round=round_obj)
        
        time_remaining = int((team_round.end_time - timezone.now()).total_seconds())
        
        return JsonResponse({
            'team_name': team.team_name,
            'current_score': team_round.score,
            'time_remaining': max(0, time_remaining),
            'current_page': team_round.current_page,
            'status': team_round.status
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)