from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<int:pk>/export/', views.project_export, name='project_export'),
    path('projects/<int:pk>/add-team-members/', views.add_team_members, name='add_team_members'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
] 