from django.urls import path
from . import views
from . import api_views

app_name = 'team'

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.TeamCreateView.as_view(), name='team_create'),
    path('management/', views.TeamManagementView.as_view(), name='team_management'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('<int:pk>/add-member/', views.add_team_member, name='add_member'),
    path('<int:pk>/remove-member/<int:user_id>/', views.remove_team_member, name='remove_member'),
    path('<int:pk>/delete/', views.delete_team, name='delete_team'),
    path('invite/', views.invite_team_member, name='team_invite'),
    path('assign-projects/', views.assign_projects, name='team_assign_projects'),
    path('cancel-invite/', views.cancel_invite, name='team_cancel_invite'),
    path('update-role/', views.update_role, name='team_update_role'),
    path('user-projects/<int:user_id>/', views.get_user_projects, name='user_projects'),
    # API endpoints
    path('api/members/', api_views.TeamMemberListAPI.as_view(), name='api_team_members'),
    path('api/projects/<int:user_id>/', api_views.UserProjectsAPI.as_view(), name='api_user_projects'),
    path('api/stats/', api_views.TeamStatsAPI.as_view(), name='api_team_stats'),
    path('api/project/<int:project_id>/members/', api_views.ProjectMembersAPI.as_view(), name='api_project_members'),
] 