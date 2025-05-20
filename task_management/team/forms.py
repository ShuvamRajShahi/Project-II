from django import forms
from .models import Team

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'name': 'Enter a unique name for your team.',
            'description': 'Provide a brief description of the team and its purpose.',
        } 