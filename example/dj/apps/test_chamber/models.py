from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError

from chamber.models import ModelDiffMixin, SmartModel, ComparableModelMixin


class ShortcutsModel(models.Model):
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    number = models.IntegerField()


class DiffModel(ModelDiffMixin, models.Model):
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
