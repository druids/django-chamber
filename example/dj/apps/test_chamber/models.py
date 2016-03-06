from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError

from chamber.models import ModelDiffMixin, SmartModel, ComparableModelMixin
from chamber.exceptions import PersistenceException


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
    number = models.IntegerField()

    def clean_name(self):
        if len(self.name) < 10:
            raise ValidationError('Name must be longer than 10 chars')

    def pre_save(self, changed, *args, **kwargs):
        if not changed:
            self.number = 11

    def post_save(self, changed, changed_fields, *args, **kwargs):
        if 'number' in changed_fields:
            raise PersistenceException('number cannot be changed')

    class Meta:
        abstract = True


class CleanedSmartModel(TestSmartModel):
    pass


class NotCleanedSmartModel(TestSmartModel):

    class SmartMeta:
        clean_before_save = False


class BackendUser(AbstractBaseUser):
    pass


class FrontendUser(AbstractBaseUser):
    pass
