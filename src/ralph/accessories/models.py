from dj.choices import Choices
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
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
    user = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name='+',
        help_text=_('User of the accessories'),
        on_delete=models.SET_NULL
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
        verbose_name=_('number of purchased items'),
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT
    )

    @cached_property
    def used(self):
        if not self.pk:
            return 0
        try:
            # try use fields from objects_used_free manager
            return (self.user_count or 0) + (self.baseobject_count or 0)
        except AttributeError:
            base_objects_qs = self.base_objects.through.objects.filter(
                Accessories=self
            )
            users_qs = self.users.through.objects.filter(Accessories=self)

            def get_sum(qs):
                return qs.aggregate(sum=Sum('quantity'))['sum'] or 0
            return sum(map(get_sum, [base_objects_qs, users_qs]))
    used._permission_field = 'number_bought'

    @cached_property
    def free(self):
        if not self.pk:
            return 0
        return self.number_bought - self.used
    free._permission_field = 'number_bought'
