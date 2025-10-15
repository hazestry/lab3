from django.db import models

class TourRoute(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    length_km = models.FloatField()
    difficulty = models.CharField(max_length=50)

    def __str__(self):
        return self.name
