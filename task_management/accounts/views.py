from django.shortcuts import render
from django.views.generic import CreateView, DetailView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, UserSettingsForm
from django.contrib.auth import logout, authenticate
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# Create your views here.

class SignUpView(CreateView):
    model = CustomUser
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully. Please log in.')
        return response

class ProfileView(LoginRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assigned_tasks'] = self.object.assigned_tasks.all()
        context['managed_projects'] = self.object.managed_projects.all()
        return context

class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserSettingsForm
    template_name = 'accounts/settings.html'
    success_url = reverse_lazy('accounts:settings')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Settings updated successfully.')
        return super().form_valid(form)

@login_required
def custom_logout(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
    return redirect('projects:dashboard')

@login_required
def deactivate_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = authenticate(username=request.user.username, password=password)
        
        if user is not None:
            # Deactivate the account
            user.is_active = False
            user.save()
            logout(request)
            messages.success(request, 'Your account has been deactivated.')
            return redirect('login')
        else:
            messages.error(request, 'Invalid password. Please try again.')
            return redirect('accounts:settings')
    
    return redirect('accounts:settings')
