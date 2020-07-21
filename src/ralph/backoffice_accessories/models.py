from dj.choices import Choices

from ralph.accounts.models import Regionalizable, RalphUser
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from django.db import models
from django.conf import settings
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions


class AccessoriesStatus(Choices):
    _ = Choices.Choice

    new = _('new')
    in_progress = _('in progress')
    lost = _('lost')
    damaged = _('damaged')
    used = _('in use')
    free = _('free')
    return_in_progress = _('return in progress')
    liquidated = _('liquidated')
    reserved = _("reserved")

class Accessories(
    AdminAbsoluteUrlMixin,
    TimeStampMixin,
    Regionalizable,
    models.Model,
    metaclass=TransitionWorkflowBaseWithPermissions
):

    manufacturer = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Manufacturer of accessories')
    )
    accessories_type = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Type of accessories')
    )
    accessories_name = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Name of accessories')
    )
    produckt_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Number of accessories')
    )
    user = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=_('User of the accesories'),
        on_delete=models.SET_NULL
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=('Owner of the accesories'),
        on_delete=models.SET_NULL
    )
    status = TransitionField(
        choices=AccessoriesStatus(),
        default=AccessoriesStatus.new.id,
        null=False,
        blank=False,
        help_text=_('Accesories status')
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_owner',
    )
    number_bought = models.IntegerField(
        verbose_name=_('number of purchased items'),
    )
