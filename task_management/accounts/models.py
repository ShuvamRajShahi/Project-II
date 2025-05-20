from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.templatetags.static import static

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('MANAGER', 'Project Manager'),
        ('MEMBER', 'Team Member'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='MEMBER')
    phone = models.CharField(max_length=15, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    
    def is_manager(self):
        return self.user_type == 'MANAGER'
    
    @property
    def profile_picture_url(self):
        if bool(self.profile_picture):  # Check if field has a file
            try:
                return self.profile_picture.url
            except (ValueError, AttributeError):
                pass
        return static('images/default-profile.png')
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"