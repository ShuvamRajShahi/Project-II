from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime, time
from .models import Task, Comment, TimeEntry
from projects.models import Project
from .forms import TaskForm, CommentForm, TimeEntryForm

User = get_user_model()

class TaskManagementTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.manager = User.objects.create_user(
            username='manager', 
            password='testpass123',
            user_type='MANAGER'
        )
        self.employee = User.objects.create_user(
            username='employee', 
            password='testpass123',
            user_type='MEMBER'
        )
        
        # Create test project
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            manager=self.manager,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=30)).date()
        )
        self.project.team_members.add(self.employee)
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            project=self.project,
            assigned_to=self.employee,
            created_by=self.manager,
            due_date=timezone.now() + timedelta(days=7),
            status='todo',
            priority='medium',
            estimated_hours=10
        )

    def test_task_creation(self):
        """Test task creation"""
        self.client.login(username='manager', password='testpass123')
        # Calculate a due date that's within the project's timeline
        project_start = self.project.start_date
        project_end = self.project.end_date
        due_date = project_start + timedelta(days=1)  # One day after project start
        
        response = self.client.post(
            reverse('tasks:task_create'),
            {
                'title': 'New Task',
                'description': 'New task description',
                'project': self.project.id,
                'assigned_to': self.employee.id,
                'due_date': datetime.combine(due_date, time(12, 0)).strftime('%Y-%m-%dT%H:%M'),  # Noon on the due date
                'status': 'todo',
                'priority': 'medium',
                'estimated_hours': 10
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Task.objects.count(), 2)

    def test_task_status_update(self):
        """Test task status update"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('tasks:update_status', kwargs={'pk': self.task.pk}),
            {'status': 'in_progress'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')

    def test_comment_creation(self):
        """Test comment creation"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('tasks:add_comment', kwargs={'pk': self.task.pk}),
            {'content': 'Test comment'}
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(self.task.task_comments.count(), 1)
        self.assertEqual(self.task.task_comments.first().content, 'Test comment')

    def test_time_entry_creation(self):
        """Test time entry creation"""
        self.client.login(username='employee', password='testpass123')
        start_time = timezone.now()
        end_time = start_time + timedelta(hours=2)
        response = self.client.post(
            reverse('tasks:add_time_entry', kwargs={'pk': self.task.pk}),
            {
                'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'description': 'Test time entry'
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(self.task.task_time_entries.count(), 1)
        time_entry = self.task.task_time_entries.first()
        self.assertEqual(time_entry.duration, 2.0)  # 2 hours

    def test_task_detail_view(self):
        """Test task detail view access"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_detail.html')

    def test_task_list_view(self):
        """Test task list view"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasks/task_list.html')

    def test_task_create_permission(self):
        """Test task creation permission"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to task list

    def test_task_form_validation(self):
        """Test task form validation"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.post(
            reverse('tasks:task_create'),
            {'title': ''}  # Empty title should fail validation
        )
        self.assertEqual(response.status_code, 200)  # Stay on form
        self.assertContains(response, 'This field is required')  # Check for error message

    def test_comment_form_validation(self):
        """Test comment form validation"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('tasks:add_comment', kwargs={'pk': self.task.pk}),
            {'content': ''}  # Empty content should fail validation
        )
        self.assertEqual(response.status_code, 302)  # Redirects back with error message

    def test_unauthorized_task_access(self):
        """Test unauthorized access to task detail"""
        # Create a new user not in the project team
        other_user = get_user_model().objects.create_user(
            username='other',
            password='testpass123',
            user_type='MEMBER'
        )
        self.client.login(username='other', password='testpass123')
        response = self.client.get(reverse('tasks:task_detail', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 403)  # Should be forbidden
