from django.db import models

# Create your models here.

class CorpusEntry(models.Model):
    index = models.IntegerField(primary_key=True, unique=True, null=False)
    text = models.TextField()

    def __str__(self):
        return self.text