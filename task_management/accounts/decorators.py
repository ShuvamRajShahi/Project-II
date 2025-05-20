from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_manager():
            return view_func(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page. Manager access required.")
        return redirect('dashboard')
    return _wrapped_view

def manager_or_assigned_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_manager():
                return view_func(request, *args, **kwargs)
            # Check if user is assigned to the project/task
            # This part needs to be customized based on your view
            return view_func(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('login')
    return _wrapped_view 