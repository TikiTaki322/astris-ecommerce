from django.db import models

from .user import UserProfile


class UserLoginHistory(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='login_history')
    email = models.EmailField(max_length=40, blank=True, null=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)