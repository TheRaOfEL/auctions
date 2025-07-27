# Create your models here.
import uuid

from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    username = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    profile_picture = models.ImageField(upload_to='profile/',
                                        default='client-circle4.png', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.username)
