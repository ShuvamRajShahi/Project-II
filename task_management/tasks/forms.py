from django import forms
from .models import Task, Comment, TimeEntry
from projects.models import Project
from django.contrib.auth import get_user_model
from django.db import models
from datetime import datetime, time
from django.utils import timezone

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'project', 'title', 'description', 'assigned_to', 
            'due_date', 'status', 'priority', 'estimated_hours'
        ]
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'estimated_hours': forms.NumberInput(attrs={'step': '0.5'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        
        # Filter projects based on user's role
        if user.is_manager():
            # Get all teams managed by the user
            managed_teams = user.managed_teams.all()
            self.fields['project'].queryset = Project.objects.filter(manager=user)
            
            # Get all team members from the teams managed by the user
            # Include both team members and the manager
            self.fields['assigned_to'].queryset = User.objects.filter(
                models.Q(teams__in=managed_teams) |  # Team members
                models.Q(id=user.id)  # Include the manager themselves
            ).distinct()
            
            # If a project is selected, filter users to project team members
            if self.data.get('project'):
                try:
                    project = Project.objects.get(id=self.data['project'])
                    self.fields['assigned_to'].queryset = User.objects.filter(
                        models.Q(id__in=project.team_members.values_list('id', flat=True)) |
                        models.Q(id=project.manager.id)
                    ).distinct()
                except (Project.DoesNotExist, ValueError):
                    pass
        else:
            # For team members, show only projects they are part of
            self.fields['project'].queryset = Project.objects.filter(team_members=user)
            
            # For assigned_to, initially set an empty queryset
            self.fields['assigned_to'].queryset = User.objects.none()
            
            # If a project is selected, show only team members of that project
            if self.instance and self.instance.project_id:
                project = self.instance.project
                self.fields['assigned_to'].queryset = User.objects.filter(
                    models.Q(id__in=project.team_members.values_list('id', flat=True)) |
                    models.Q(id=project.manager.id)
                ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        assigned_to = cleaned_data.get('assigned_to')
        due_date = cleaned_data.get('due_date')

        if project:
            # Validate due date is within project timeline
            if due_date:
                # Make due_date timezone-aware if it isn't already
                if timezone.is_naive(due_date):
                    due_date = timezone.make_aware(due_date)

                # Convert project dates to timezone-aware datetime for comparison
                if project.start_date:
                    project_start = timezone.make_aware(
                        datetime.combine(project.start_date, time.min)
                    )
                    if due_date < project_start:
                        self.add_error('due_date', 'Task due date cannot be earlier than project start date.')
                
                if project.end_date:
                    project_end = timezone.make_aware(
                        datetime.combine(project.end_date, time.max)
                    )
                    if due_date > project_end:
                        self.add_error('due_date', 'Task due date cannot be later than project end date.')

            # Validate assigned user is part of the project team
            if assigned_to:
                is_valid_assignee = (
                    assigned_to in project.team_members.all() or  # Is team member
                    assigned_to == project.manager  # Is project manager
                )
                
                if not is_valid_assignee:
                    self.add_error('assigned_to', 'User must be a member or manager of the project.')

        return cleaned_data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment here...'})
        }

class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['start_time', 'end_time', 'description']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'What did you work on?'})
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError("End time must be after start time.")
        
        return cleaned_data 