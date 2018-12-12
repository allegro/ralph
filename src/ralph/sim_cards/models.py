from dj.choices import Choices
from django.conf import settings
from django.core.validators import (
    MaxLengthValidator,
    MinLengthValidator,
    RegexValidator
)
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.transitions.fields import TransitionField


PUK_CODE_VALIDATORS = [
    MinLengthValidator(5),
    RegexValidator(
        regex='^\d+$',
        message=_('Required numeric characters only.')
    ),
]


PIN_CODE_VALIDATORS = [
    MinLengthValidator(4),
    RegexValidator(
        regex='^\d+$',
        message=_('Required numeric characters only.')
    ),
]


class SIMCardStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    in_progress = _("in progress")
    waiting_for_release = _("waiting for release")
    used = _("in use")
    damaged = _("damaged")
    liquidated = _("liquidated")
    free = _("free")
    reserved = _("reserved")
    loan_in_progress = _("loan in progress")
    return_in_progress = _("return in progress")
    in_quarantine = _("in quarantine")


class CellularCarrier(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    pass


class SIMCardFeatures(
    AdminAbsoluteUrlMixin,
    NamedMixin,
    models.Model
):
    pass


class SIMCard(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    pin1 = models.CharField(
        max_length=8, null=True, blank=True,
        help_text=_('Required numeric characters only.'),
        validators=PIN_CODE_VALIDATORS
    )
    puk1 = models.CharField(
        max_length=16, help_text=_('Required numeric characters only.'),
        validators=PUK_CODE_VALIDATORS
    )
    pin2 = models.CharField(
        max_length=8, null=True, blank=True,
        help_text=_('Required numeric characters only.'),
        validators=PIN_CODE_VALIDATORS
    )
    puk2 = models.CharField(
        max_length=16, null=True, blank=True,
        help_text=_('Required numeric characters only.'),
        validators=PUK_CODE_VALIDATORS)
    carrier = models.ForeignKey(
        CellularCarrier, on_delete=models.PROTECT,
    )
    card_number = models.CharField(
        max_length=22, unique=True,
        validators=[
            MinLengthValidator(1),
            MaxLengthValidator(22),
            RegexValidator(
                regex='^\d+$',
                message=_('Required numeric characters only.'),
            )
        ]
    )
    phone_number = models.CharField(
        max_length=16, unique=True, help_text=_('ex. +2920181234'),
        validators=[
            MinLengthValidator(1),
            MaxLengthValidator(16),
            RegexValidator(
                regex='^\+\d+$',
                message='Phone number must have +2920181234 format.'
            )
        ]
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_simcards',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='used_simcards',
    )
    status = TransitionField(
        default=SIMCardStatus.new.id,
        choices=SIMCardStatus(),
    )
    remarks = models.TextField(blank=True)
    quarantine_until = models.DateField(
        null=True, blank=True,
        help_text=_('End of quarantine date.')
    )
    features = models.ManyToManyField(
        SIMCardFeatures,
        blank=True,
    )

    def __str__(self):
        return _('SIM Card: {}').format(self.phone_number)
