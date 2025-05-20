from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('create/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    
    # Task execution endpoints
    path('<int:pk>/status/', views.update_task_status, name='update_status'),
    path('<int:pk>/add-time/', views.add_time_entry, name='add_time_entry'),
    path('time-entry/<int:pk>/delete/', views.delete_time_entry, name='delete_time_entry'),
    
    # Attachment endpoints
    path('<int:pk>/attachment/', views.add_attachment, name='add_attachment'),
    path('<int:task_pk>/attachment/<int:attachment_pk>/delete/', views.delete_attachment, name='delete_attachment'),
] 