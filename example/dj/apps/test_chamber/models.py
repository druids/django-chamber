from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.translation import ugettext_lazy as _

from chamber import models as chamber_models
from chamber.models import fields as chamber_fields
from chamber.models.dispatchers import CreatedDispatcher, PropertyDispatcher, StateDispatcher
from chamber.models.signals import dispatcher_pre_save, dispatcher_post_save
from chamber.utils.datastructures import ChoicesNumEnum, SequenceChoicesNumEnum, SubstatesChoicesNumEnum

from .handlers import (
    create_test_dispatchers_model_handler, create_test_fields_model_handler, create_test_smart_model_handler,
    create_csv_record_handler, OneTimeStateChangedHandler
)


class ShortcutsModel(models.Model):
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    number = models.IntegerField()


class DiffModel(chamber_models.SmartModel):
    name = models.CharField(max_length=100)
    datetime = models.DateTimeField()
    number = models.IntegerField()


class ComparableModel(chamber_models.ComparableModelMixin, models.Model):
    name = models.CharField(max_length=100)


class TestSmartModel(chamber_models.SmartModel):
    name = models.CharField(max_length=100)


class RelatedSmartModel(chamber_models.SmartModel):
    test_smart_model = models.ForeignKey(TestSmartModel, related_name='test_smart_models', on_delete=models.CASCADE)


class BackendUser(AbstractBaseUser):
    pass


class FrontendUser(AbstractBaseUser):
    pass


class CSVRecord(chamber_models.SmartModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    number = models.IntegerField(null=True, blank=True)


class TestFieldsModel(chamber_models.SmartModel):

    STATE = ChoicesNumEnum(
        ('OK', _('ok'), 1),
        ('NOT_OK', _('not ok'), 2),
    )

    STATE_REASON = SubstatesChoicesNumEnum({
        STATE.OK: (
            ('SUB_OK_1', _('1st substate'), 1),
            ('SUB_OK_2', _('2nd substate'), 2),
        ),
        STATE.NOT_OK: (
            ('SUB_NOT_OK_1', _('1st not ok substate'), 3),
            ('SUB_NOT_OK_2', _('2nd not ok substate'), 4),
        ),
    })

    GRAPH = SequenceChoicesNumEnum((
        ('FIRST', _('first'), 1, ('SECOND',)),
        ('SECOND', _('second'), 2, ('THIRD',)),
        ('THIRD', _('third'), 3, ()),
    ), initial_states=('FIRST',))

    decimal = chamber_fields.DecimalField(null=True, blank=True, min=3, max=10, max_digits=5, decimal_places=3)
    state = models.IntegerField(null=True, blank=False, choices=STATE.choices, default=STATE.OK)
    state_reason = chamber_models.SubchoicesPositiveIntegerField(null=True, blank=True, enum=STATE_REASON,
                                                                 supchoices_field_name='state',
                                                                 default=STATE_REASON.SUB_OK_1)
    state_prev = chamber_models.PrevValuePositiveIntegerField(verbose_name=_('previous state'), null=False, blank=False,
                                                              copy_field_name='state', choices=STATE.choices,
                                                              default=STATE.NOT_OK)
    state_graph = chamber_models.EnumSequencePositiveIntegerField(verbose_name=_('graph'), null=True, blank=True,
                                                                  enum=GRAPH)
    file = chamber_models.FileField(verbose_name=_('file'), null=True, blank=True,
                                    allowed_content_types=('application/pdf', 'text/plain', 'text/csv'))
    image = chamber_models.ImageField(verbose_name=_('image'), null=True, blank=True, max_upload_size=1)
    price = chamber_models.PriceField(verbose_name=_('price'), null=True, blank=True, currency=_('EUR'))
    total_price = chamber_models.PositivePriceField(verbose_name=_('total price'), null=True, blank=True)


class TestDispatchersModel(chamber_models.SmartModel):

    STATE = ChoicesNumEnum(
        ('FIRST', _('first'), 1),
        ('SECOND', _('second'), 2),
    )
    state = models.IntegerField(null=True, blank=False, choices=STATE.choices, default=STATE.FIRST)

    dispatchers = (
        CreatedDispatcher(create_csv_record_handler, signal=dispatcher_pre_save),
        StateDispatcher(create_test_smart_model_handler, STATE, state, STATE.SECOND, signal=dispatcher_pre_save),
        PropertyDispatcher(create_test_fields_model_handler, 'always_dispatch', signal=dispatcher_post_save),
        PropertyDispatcher(create_test_dispatchers_model_handler, 'never_dispatch', signal=dispatcher_post_save),
        OneTimeStateChangedHandler(),
    )

    @property
    def always_dispatch(self):
        return True

    @property
    def never_dispatch(self):
        return False


class TestOnDispatchModel(chamber_models.SmartModel):
    pass
