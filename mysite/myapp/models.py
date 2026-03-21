from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('employer', 'Работодатель'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    university = models.CharField(max_length=100, blank=True)

    class Meta:
        swappable = 'AUTH_USER_MODEL'
