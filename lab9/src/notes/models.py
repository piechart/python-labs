from django.db import models
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User

class Note(models.Model):
    title = models.CharField(max_length=200)
    tags = models.CharField(max_length=100)
    body = models.TextField()
    pub_date = models.DateTimeField('date published')
    owner = models.ForeignKey(User, related_name='notes', on_delete=models.CASCADE, default=1)

    def was_published_recently(self):
        now = timezone.now()
        return now - timedelta(days=1) <= self.pub_date <= now
