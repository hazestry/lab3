from django.db import models

class TourRoute(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    length_km = models.FloatField()
    difficulty = models.CharField(max_length=50)
    members_count = models.IntegerField()

    def __str__(self):
        return self.name
