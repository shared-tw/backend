from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Profile(models.Model):
    line_id = models.CharField(max_length=128, unique=True)
    display_name = models.CharField(max_length=256)
    picture_url = models.URLField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
