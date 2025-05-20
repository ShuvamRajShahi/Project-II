from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
import csv
from .models import Project
from team.models import Team
from .forms import ProjectForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Count, Q, Case, When, ExpressionWrapper, IntegerField
from tasks.models import Task
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.shortcuts import redirect

User = get_user_model()

# Create your views here.

@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_manager():
            # Manager's dashboard
            managed_projects = Project.objects.filter(manager=user)
            context.update({
                'active_projects_count': managed_projects.filter(Q(status='in_progress') | Q(status='planning')).count(),
                'team_members_count': User.objects.filter(teams__manager=user).distinct().count(),
                'completed_tasks_count': Task.objects.filter(project__manager=user, status='completed').count(),
                'pending_tasks_count': Task.objects.filter(project__manager=user).exclude(status='completed').count(),
                'projects': managed_projects.order_by('-created_at')[:5],
                'tasks': Task.objects.filter(project__manager=user).order_by('-created_at')[:5],
            })
        else:
            # Team member's dashboard
            tasks = Task.objects.filter(
                Q(assigned_to=user) | 
                Q(project__team_members=user)
            ).distinct()
            
            context.update({
                'completed_tasks_count': tasks.filter(status='completed').count(),
                'pending_tasks_count': tasks.exclude(status='completed').count(),
                'tasks': tasks.order_by('-created_at')[:5],
                'user_projects': Project.objects.filter(team_members=user).order_by('-created_at')
            })

        return context

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 9

    def get_queryset(self):
        queryset = Project.objects.filter(
            Q(manager=self.request.user) | Q(team_members=self.request.user)
        ).distinct()
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-created_at')

class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project_list')

    def test_func(self):
        return self.request.user.is_manager

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.fields.get('team_members'):
            # Get all teams managed by the user
            managed_teams = Team.objects.filter(manager=self.request.user)
            # Get all team members from those teams
            team_members = User.objects.filter(teams__in=managed_teams).distinct().exclude(
                id=self.request.user.id
            )
            form.fields['team_members'].queryset = team_members
        return form

    def form_valid(self, form):
        form.instance.manager = self.request.user
        messages.success(self.request, 'Project created successfully.')
        return super().form_valid(form)

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

    def test_func(self):
        project = self.get_object()
        return (self.request.user == project.manager or 
                self.request.user in project.team_members.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = self.object.tasks.all()
        
        # Only show users from the same team as the project manager
        if self.request.user.is_manager:
            manager_teams = Team.objects.filter(manager=self.request.user)
            team_members = User.objects.filter(teams__in=manager_teams).distinct()
            context['available_users'] = team_members.exclude(
                id__in=self.object.team_members.values_list('id', flat=True)
            ).exclude(id=self.request.user.id)
        else:
            context['available_users'] = []
            
        return context

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def test_func(self):
        return self.request.user.is_manager

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if form.fields.get('team_members'):
            # Get all teams managed by the user
            managed_teams = Team.objects.filter(manager=self.request.user)
            # Get all team members from those teams
            team_members = User.objects.filter(teams__in=managed_teams).distinct().exclude(
                id=self.request.user.id
            )
            form.fields['team_members'].queryset = team_members
        return form

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:project_list')
    template_name = 'projects/project_confirm_delete.html'

    def test_func(self):
        return self.request.user.is_manager

def project_export(request, pk):
    project = get_object_or_404(Project, pk=pk)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{project.name}_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Task', 'Assigned To', 'Status', 'Due Date', 'Time Spent'])
    
    for task in project.tasks.all():
        writer.writerow([
            task.title,
            task.assigned_to.get_full_name() if task.assigned_to else 'Unassigned',
            task.get_status_display(),
            task.due_date,
            task.total_time_spent
        ])
    
    return response

class ReportsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'projects/reports.html'

    def test_func(self):
        return self.request.user.is_manager()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        managed_projects = Project.objects.filter(manager=user)

        # Project statistics
        context['project_stats'] = {
            'total': managed_projects.count(),
            'active': managed_projects.filter(status='in_progress').count(),
            'completed': managed_projects.filter(status='completed').count(),
            'on_hold': managed_projects.filter(status='on_hold').count(),
        }

        # Task statistics
        tasks = Task.objects.filter(project__manager=user)
        context['task_stats'] = {
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'pending': tasks.filter(status='todo').count(),
        }

        # Team statistics
        context['team_stats'] = {
            'total_members': User.objects.filter(assigned_projects__manager=user).distinct().count(),
            'projects_by_member': Project.objects.filter(manager=user).values('team_members__username').annotate(count=Count('id')),
        }

        return context

@login_required
def add_team_members(request, pk):
    if not request.user.is_manager:
        messages.error(request, "You don't have permission to modify team members.")
        return redirect('projects:project_detail', pk=pk)

    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        member_ids = request.POST.getlist('team_members')
        project.team_members.set(member_ids)
        messages.success(request, "Team members updated successfully.")
    
    return redirect('projects:project_detail', pk=pk)
