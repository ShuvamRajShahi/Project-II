from django.shortcuts import render
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Task, Comment, TimeEntry, Attachment
from projects.models import Project
from .forms import TaskForm, CommentForm, TimeEntryForm
import json
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied

# Create your views here.

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10

    def get_queryset(self):
        queryset = Task.objects.all()
        
        # Filter by project if specified
        project_id = self.request.GET.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        
        # Filter by status if specified
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by priority if specified
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        user = self.request.user
        # Get all projects where user is either a manager or team member
        managed_projects = Project.objects.filter(manager=user)
        team_projects = user.assigned_projects.all()
        
        # Combine conditions for tasks visibility
        queryset = queryset.filter(
            Q(assigned_to=user) |  # Tasks assigned to user
            Q(project__in=managed_projects) |  # Tasks in projects they manage
            Q(project__in=team_projects)  # Tasks in projects where they're a team member
        ).distinct()
            
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # Show all relevant projects in the filter dropdown
        context['projects'] = Project.objects.filter(
            Q(manager=user) |
            Q(team_members=user)
        ).distinct()
        context['status_choices'] = Task.STATUS_CHOICES
        context['priority_choices'] = Task.PRIORITY_CHOICES
        return context

class TaskCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')

    def test_func(self):
        return self.request.user.is_manager()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Task created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form data:", self.request.POST)  # Debug print
        print("Form errors:", form.errors)  # Debug print
        return super().form_invalid(form)

    def handle_no_permission(self):
        messages.error(self.request, "Only managers can create tasks.")
        return redirect('tasks:task_list')

class TaskDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        # Allow access if user is:
        # 1. The project manager
        # 2. The assigned user
        # 3. A team member of the project
        return (user == task.project.manager or 
                user == task.assigned_to or 
                user in task.project.team_members.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        print("Task ID:", task.id)  # Debug print
        print("Number of comments:", task.task_comments.count())  # Debug print
        print("Comments:", list(task.task_comments.all().values('id', 'content', 'user__username')))  # Debug print
        context['comment_form'] = CommentForm()
        context['time_entry_form'] = TimeEntryForm()
        context['status_choices'] = Task.STATUS_CHOICES
        return context

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if 'save_and_continue' in self.request.POST:
            return reverse_lazy('tasks:task_edit', kwargs={'pk': self.object.pk})
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.pk})

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    success_url = reverse_lazy('tasks:task_list')
    template_name = 'tasks/task_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Task deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
def add_comment(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        print("Form data:", request.POST)  # Debug print
        form = CommentForm(request.POST)
        if form.is_valid():
            print("Form is valid")  # Debug print
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            print("Comment saved with ID:", comment.id)  # Debug print
            print("Comment content:", comment.content)  # Debug print
            print("Associated task ID:", comment.task.id)  # Debug print
            messages.success(request, 'Comment added successfully.')
        else:
            print("Form errors:", form.errors)  # Debug print
            messages.error(request, 'Error adding comment.')
    return redirect('tasks:task_detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Only assigned user can update status
    if request.user != task.assigned_to:
        raise PermissionDenied("Only the assigned user can update the task status.")
    
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save()
            
            # Add a comment about the status change
            Comment.objects.create(
                task=task,
                user=request.user,
                content=f"Status changed to {task.get_status_display()}",
                created_at=timezone.now()
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Task status updated to {task.get_status_display()}'
            })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid status value'
    }, status=400)

@login_required
@require_http_methods(["POST"])
def add_time_entry(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Only assigned user can add time entries
    if request.user != task.assigned_to:
        raise PermissionDenied("Only the assigned user can add time entries for this task.")
    
    form = TimeEntryForm(request.POST)
    if form.is_valid():
        time_entry = form.save(commit=False)
        time_entry.task = task
        time_entry.user = request.user
        time_entry.save()
        messages.success(request, 'Time entry added successfully.')
    else:
        messages.error(request, 'Invalid time entry data.')
    
    return redirect('tasks:task_detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def delete_time_entry(request, pk):
    time_entry = get_object_or_404(TimeEntry, pk=pk)
    
    # Only the user who created the entry can delete it
    if request.user != time_entry.user:
        raise PermissionDenied("Only the user who created the time entry can delete it.")
    
    task_id = time_entry.task.id
    time_entry.delete()
    messages.success(request, 'Time entry deleted successfully.')
    
    return redirect('tasks:task_detail', pk=task_id)

@login_required
def get_project_members(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Get team members and project manager
    members = list(project.team_members.all())
    if project.manager not in members:
        members.append(project.manager)
    
    # Format the data for the response
    members_data = [
        {
            'id': member.id,
            'name': member.get_full_name() or member.username
        }
        for member in members
    ]
    
    return JsonResponse(members_data, safe=False)

@login_required
def get_project_tasks(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    tasks = project.project_tasks.exclude(id=request.GET.get('exclude_id'))
    data = [{'id': task.id, 'title': task.title} for task in tasks]
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(["POST"])
def add_attachment(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Only assigned user or project manager can add attachments
    if request.user != task.assigned_to and request.user != task.project.manager:
        raise PermissionDenied("Only the assigned user or project manager can add attachments.")
    
    if request.FILES:
        file = request.FILES['file']
        description = request.POST.get('description', '')
        
        attachment = Attachment.objects.create(
            task=task,
            user=request.user,
            file=file,
            filename=file.name
        )
        
        messages.success(request, 'File uploaded successfully.')
    else:
        messages.error(request, 'No file was uploaded.')
    
    return redirect('tasks:task_detail', pk=pk)

@login_required
@require_http_methods(["POST"])
def delete_attachment(request, task_pk, attachment_pk):
    attachment = get_object_or_404(Attachment, pk=attachment_pk, task_id=task_pk)
    
    # Only the user who uploaded the file or project manager can delete it
    if request.user != attachment.user and request.user != attachment.task.project.manager:
        raise PermissionDenied("Only the user who uploaded the file or project manager can delete it.")
    
    attachment.file.delete()  # Delete the actual file
    attachment.delete()  # Delete the database record
    messages.success(request, 'File deleted successfully.')
    
    return redirect('tasks:task_detail', pk=task_pk)

@login_required
def get_project_dates(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Format dates in ISO format for the datetime-local input
    start_date = project.start_date.isoformat() if project.start_date else None
    end_date = project.end_date.isoformat() if project.end_date else None
    
    return JsonResponse({
        'start_date': start_date,
        'due_date': end_date  # Keep 'due_date' in response for the form field
    })
