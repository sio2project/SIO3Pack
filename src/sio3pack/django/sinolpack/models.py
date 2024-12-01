from django.db import models


class SinolpackPackage(models.Model):
    """
    A package for the sinolpack package type.
    """
    problem_id = models.IntegerField()
    short_name = models.CharField(max_length=100)
