from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser
from projects.models import Project
from team.models import Team

class TeamMemberListAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager

    def get(self, request):
        """Return list of team members with basic info"""
        # Get all teams managed by the user
        managed_teams = Team.objects.filter(manager=request.user)
        # Get all team members from those teams
        members = CustomUser.objects.filter(teams__in=managed_teams).distinct().exclude(
            id=request.user.id
        ).values(
            'id', 
            'first_name', 
            'last_name', 
            'email', 
            'user_type',
            'is_active'
        )
        
        # Format the data for frontend
        member_list = [{
            'id': member['id'],
            'name': f"{member['first_name']} {member['last_name']}",
            'email': member['email'],
            'role': member['user_type'],
            'is_active': member['is_active']
        } for member in members]
        
        return JsonResponse({'members': member_list})

class UserProjectsAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager

    def get(self, request, user_id):
        """Return list of projects assigned to a specific user"""
        user = get_object_or_404(CustomUser, id=user_id)
        projects = user.assigned_projects.values('id', 'name')
        return JsonResponse({'projects': list(projects)})

class TeamStatsAPI(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_manager

    def get(self, request):
        """Return team statistics"""
        from django.db.models import Count, Q
        from tasks.models import Task
        
        # Get basic stats
        total_members = CustomUser.objects.count()
        active_projects = Project.objects.filter(status='in_progress').count()
        completed_tasks = Task.objects.filter(status='completed').count()
        total_tasks = Task.objects.count()
        
        # Get workload distribution
        workload = Task.objects.filter(
            status__in=['todo', 'in_progress']
        ).values(
            'assigned_to__first_name',
            'assigned_to__last_name'
        ).annotate(
            task_count=Count('id')
        )
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return JsonResponse({
            'total_members': total_members,
            'active_projects': active_projects,
            'completion_rate': round(completion_rate, 2),
            'workload': list(workload)
        })

class ProjectMembersAPI(LoginRequiredMixin, View):
    def get(self, request, project_id):
        """Return list of members for a specific project"""
        project = get_object_or_404(Project, id=project_id)
        
        # Check if user has access to this project
        if not (request.user.is_manager or request.user in project.team_members.all()):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        members = project.team_members.values(
            'id',
            'first_name',
            'last_name',
            'email',
            'user_type'
        )
        
        return JsonResponse({'members': list(members)}) 