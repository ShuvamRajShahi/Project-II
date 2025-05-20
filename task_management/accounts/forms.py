from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type')
        widgets = {
            'user_type': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_type'].help_text = 'Select your role in the system.'
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

class CustomUserChangeForm(UserChangeForm):
    password = None  # Remove password field from form

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'bio', 'profile_picture')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone')