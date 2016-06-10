from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractBaseUser

from chamber.models import SmartModel, ComparableModelMixin


class ShortcutsModel(models.Model):
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    number = models.IntegerField()


class DiffModel(SmartModel):
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    number = models.IntegerField()


class ComparableModel(ComparableModelMixin, models.Model):
    name = models.CharField(max_length=100)


class TestSmartModel(SmartModel):
    name = models.CharField(max_length=100)


class BackendUser(AbstractBaseUser):
    pass


class FrontendUser(AbstractBaseUser):
    pass
