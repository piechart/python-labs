from django.db import models
from datetime import timedelta
from django.utils import timezone

class Note(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    pub_date = models.DateTimeField('date published')

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - timedelta(days=1)
