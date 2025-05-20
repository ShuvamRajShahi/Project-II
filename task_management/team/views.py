from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from .models import TeamInvitation, Team, TeamJoinRequest
from accounts.models import CustomUser
from projects.models import Project
from tasks.models import Task
from .forms import TeamForm
import json
from django.utils import timezone
from django.utils.html import strip_tags

class TeamManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'team/team_management.html'
    context_object_name = 'team_members'

    def test_func(self):
        return self.request.user.is_manager

    def get_queryset(self):
        # Get all teams managed by the user
        managed_teams = Team.objects.filter(manager=self.request.user)
        # Get all team members from those teams
        return CustomUser.objects.filter(teams__in=managed_teams).distinct().exclude(id=self.request.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['roles'] = CustomUser.USER_TYPE_CHOICES
        
        # Only show pending invites for the manager's teams
        managed_teams = Team.objects.filter(manager=self.request.user)
        context['pending_invites'] = TeamInvitation.objects.filter(
            team__in=managed_teams,
            is_accepted=False,
            expires_at__gt=timezone.now()
        )
        
        # Only show projects managed by this user
        context['projects'] = Project.objects.filter(manager=self.request.user)
        
        # Only count team members from manager's teams
        context['total_members'] = self.get_queryset().count()
        
        # Only count active projects managed by this user
        context['active_projects'] = Project.objects.filter(
            manager=self.request.user,
            status='in_progress'
        ).count()
        
        # Only count tasks from manager's projects
        managed_projects = Project.objects.filter(manager=self.request.user)
        context['pending_tasks'] = Task.objects.filter(
            project__in=managed_projects,
            status__in=['todo', 'in_progress']
        ).count()
        
        # Calculate completion rate for manager's tasks
        total_tasks = Task.objects.filter(project__in=managed_projects).count()
        completed_tasks = Task.objects.filter(
            project__in=managed_projects,
            status='completed'
        ).count()
        context['completion_rate'] = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        
        return context

@login_required
def invite_team_member(request):
    if not request.user.is_manager:
        messages.error(request, "You don't have permission to invite team members.")
        return redirect('team:team_management')

    if request.method == 'POST':
        email = request.POST.get('email')
        role = request.POST.get('role')
        message = request.POST.get('message', '')
        team_id = request.POST.get('team_id')
        
        # Get the team
        team = get_object_or_404(Team, id=team_id, manager=request.user)

        # Check if user already exists
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect('team:team_management')

        # Create invitation
        invitation = TeamInvitation.objects.create(
            email=email,
            role=role,
            team=team,
            invited_by=request.user,
            message=message
        )

        # Send invitation email
        context = {
            'invitation': invitation,
            'team': team,
            'signup_url': request.build_absolute_uri(
                reverse('accounts:signup') + f'?token={invitation.token}'
            )
        }
        html_message = render_to_string('team/emails/invitation.html', context)
        send_mail(
            f'Invitation to join {team.name} on TaskForce',
            strip_tags(html_message),
            None,
            [email],
            html_message=html_message
        )

        messages.success(request, f"Invitation sent to {email}")
        return redirect('team:team_management')

@login_required
def assign_projects(request):
    if not request.user.is_manager:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        project_ids = request.POST.getlist('projects')
        
        user = get_object_or_404(CustomUser, id=user_id)
        user.assigned_projects.set(project_ids)
        
        messages.success(request, f"Projects updated for {user.get_full_name()}")
        return redirect('team:team_management')

@login_required
def remove_team_member(request, pk, user_id):
    team = get_object_or_404(Team, pk=pk)
    
    # Only team manager can remove members
    if request.user != team.manager:
        messages.error(request, "You don't have permission to remove team members.")
        return redirect('team:team_detail', pk=pk)
    
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        team.team_members.remove(user)
        messages.success(request, f"{user.get_full_name()} has been removed from the team.")
        
    return redirect('team:team_detail', pk=pk)

@login_required
def cancel_invite(request):
    if not request.user.is_manager:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        invite_id = request.POST.get('invite_id')
        invitation = get_object_or_404(TeamInvitation, id=invite_id)
        invitation.delete()
        
        messages.success(request, "Invitation has been cancelled")
        return redirect('team:team_management')

@login_required
def update_role(request):
    if not request.user.is_manager:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        new_role = data.get('role')
        
        user = get_object_or_404(CustomUser, id=user_id)
        user.user_type = new_role
        user.save()
        
        return JsonResponse({'success': True})

@login_required
def get_user_projects(request, user_id):
    if not request.user.is_manager:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    user = get_object_or_404(CustomUser, id=user_id)
    projects = list(user.assigned_projects.values_list('id', flat=True))
    return JsonResponse({'projects': projects})

@login_required
def team_join_requests(request):
    # Get teams where the user is a manager
    managed_teams = Team.objects.filter(manager=request.user)
    pending_requests = TeamJoinRequest.objects.filter(
        team__in=managed_teams,
        status='PENDING'
    ).select_related('user', 'team')
    
    return render(request, 'team/join_requests.html', {
        'pending_requests': pending_requests
    })

@login_required
def process_join_request(request, request_id):
    join_request = get_object_or_404(TeamJoinRequest, id=request_id)
    
    # Verify the current user is the team manager
    if join_request.team.manager != request.user:
        messages.error(request, "You don't have permission to process this request.")
        return redirect('team:join_requests')
    
    action = request.POST.get('action')
    if action not in ['approve', 'reject']:
        messages.error(request, "Invalid action specified.")
        return redirect('team:join_requests')
    
    join_request.processed_by = request.user
    join_request.processed_at = timezone.now()
    
    if action == 'approve':
        join_request.status = 'APPROVED'
        join_request.team.team_members.add(join_request.user)
        messages.success(
            request, 
            f"{join_request.user.get_full_name()} has been added to {join_request.team.name}."
        )
    else:
        join_request.status = 'REJECTED'
        messages.info(
            request, 
            f"Join request from {join_request.user.get_full_name()} has been rejected."
        )
    
    join_request.save()
    return redirect('team:join_requests')

class TeamCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'team/team_form.html'
    success_url = reverse_lazy('team:team_list')

    def test_func(self):
        return self.request.user.is_manager()

    def form_valid(self, form):
        form.instance.manager = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, f'Team "{form.instance.name}" has been created successfully.')
        # Clear any existing messages to prevent duplicates
        storage = messages.get_messages(self.request)
        storage.used = True
        return response

@login_required
def team_list(request):
    managed_teams = Team.objects.filter(manager=request.user)
    member_teams = Team.objects.filter(team_members=request.user)
    
    context = {
        'managed_teams': managed_teams,
        'member_teams': member_teams,
    }
    return render(request, 'team/team_list.html', context)

@login_required
def request_join(request, team_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id)
        # Check if request already exists
        existing_request = TeamJoinRequest.objects.filter(
            user=request.user,
            team=team,
            status='PENDING'
        ).exists()
        
        if existing_request:
            messages.warning(request, 'You already have a pending request to join this team.')
        else:
            TeamJoinRequest.objects.create(
                user=request.user,
                team=team,
                status='PENDING'
            )
            messages.success(request, f'Request to join {team.name} has been sent to the team manager.')
        
        # Clear any existing messages to prevent duplicates
        storage = messages.get_messages(request)
        storage.used = True
    
    return redirect('team:team_list')

@login_required
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    # Only team manager or team members can view details
    if request.user != team.manager and request.user not in team.team_members.all():
        messages.error(request, "You don't have permission to view this team.")
        return redirect('team:team_list')
    
    # Get all users who are not already team members
    available_users = CustomUser.objects.exclude(
        id__in=team.team_members.values_list('id', flat=True)
    ).exclude(id=team.manager.id)
    
    context = {
        'team': team,
        'available_users': available_users,
        'is_manager': request.user == team.manager,
    }
    return render(request, 'team/team_detail.html', context)

@login_required
def add_team_member(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    # Only team manager can add members
    if request.user != team.manager:
        messages.error(request, "You don't have permission to add team members.")
        return redirect('team:team_detail', pk=pk)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        message = request.POST.get('message', '')
        
        # Check if user exists
        try:
            user = CustomUser.objects.get(email=email)
            
            # Check if user is already a member
            if user in team.team_members.all():
                messages.warning(request, f"{user.get_full_name()} is already a member of this team.")
                return redirect('team:team_detail', pk=pk)
            
            # Add user to team
            team.team_members.add(user)
            messages.success(request, f"{user.get_full_name()} has been added to the team.")
            
            # Send notification email
            context = {
                'team': team,
                'added_by': request.user,
                'message': message,
                'login_url': request.build_absolute_uri(reverse('login'))
            }
            html_message = render_to_string('team/emails/team_addition.html', context)
            send_mail(
                f'You have been added to {team.name}',
                strip_tags(html_message),
                None,
                [email],
                html_message=html_message
            )
            
        except CustomUser.DoesNotExist:
            # Create an invitation for non-existing users
            invitation = TeamInvitation.objects.create(
                email=email,
                team=team,
                invited_by=request.user,
                message=message,
                role='MEMBER'  # Default role for team members
            )
            
            # Send invitation email
            context = {
                'invitation': invitation,
                'team': team,
                'signup_url': request.build_absolute_uri(
                    reverse('accounts:signup') + f'?token={invitation.token}'
                )
            }
            html_message = render_to_string('team/emails/invitation.html', context)
            send_mail(
                f'Invitation to join {team.name} on TaskForce',
                strip_tags(html_message),
                None,
                [email],
                html_message=html_message
            )
            messages.success(request, f"Invitation sent to {email}")
    
    return redirect('team:team_detail', pk=pk)

@login_required
def delete_team(request, pk):
    team = get_object_or_404(Team, pk=pk)
    
    # Only team manager can delete the team
    if request.user != team.manager:
        messages.error(request, "You don't have permission to delete this team.")
        return redirect('team:team_list')
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Team "{team_name}" has been deleted successfully.')
        # Clear any existing messages to prevent duplicates
        storage = messages.get_messages(request)
        storage.used = True
        
    return redirect('team:team_list') 