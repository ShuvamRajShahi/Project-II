from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    path('logout/', views.custom_logout, name='logout'),
    path('deactivate/', views.deactivate_account, name='deactivate'),
] 