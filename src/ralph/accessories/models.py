import reversion
from dj.choices import Choices
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.transitions.decorators import transition_action
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
    product_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_('Number of accessories')
    )
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='AccessoriesUser',
        related_name='+'
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=_('Owner of the accessories'),
        on_delete=models.SET_NULL
    )
    status = TransitionField(
        choices=AccessoriesStatus(),
        default=AccessoriesStatus.new.id,
        null=False,
        blank=False,
        help_text=_('Accessories status')
    )
    number_bought = models.IntegerField(
        verbose_name=_('number of purchased items')
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT
    )

    @classmethod
    @transition_action(
        form_fields={
            'restock': {
                'field': forms.IntegerField(label=_('restock'),)
            }
        },
    )
    def restock(cls, instances, **kwargs):
        restock = int(kwargs['restock'])
        for instance in instances:
            instance.number_bought += restock

    @classmethod
    @transition_action(
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user',
            },
            'quantity': {
                'field': forms.IntegerField(label=_('Quantity')),
            }
        },
    )
    def release_accessories(cls, instances, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs['user']))
        AccessoriesUser.objects.create(
            user=user, quantity=kwargs['quantity'],
            accessories_id=instances[0].id
        )


@reversion.register()
class AccessoriesUser(models.Model):
    accessories = models.ForeignKey(Accessories)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('accessories', 'user')

    def __str__(self):
        return '{} of {} assigned to {}'.format(
            self.quantity, self.accessories, self.user,
        )
