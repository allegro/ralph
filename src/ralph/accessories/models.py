import reversion
from dj.choices import Choices
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.polymorphic.models import PolymorphicQuerySet
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions


_SELECT_USED_ACCESSORIES_QUERY = """
    SELECT COALESCE(SUM({assignment_table}.{quantity_column}), 0)
    FROM {assignment_table}
    WHERE {assignment_table}.{accessories_id_column} = {accessories_table}.{id_column} # noqa
"""


class AccessoriesUsedFreeManager(models.Manager):
    def get_queryset(self):
        id_column = Accessories.baseobject_ptr.field.column

        user_quantity_field = Accessories.users.through._meta.get_field('quantity') # noqa
        user_accessories_field = Accessories.users.through._meta.get_field('accessories') # noqa
        user_count_query = _SELECT_USED_ACCESSORIES_QUERY.format(
            assignment_table=Accessories.users.through._meta.db_table,
            quantity_column=user_quantity_field.db_column or user_quantity_field.column,  # noqa
            accessories_id_column=user_accessories_field.db_column or user_accessories_field,  # noqa
            accessories_table=Accessories._meta.db_table,
            id_column=id_column,
        )

        return super().get_queryset().extra(
            select={
                'user_count': user_count_query,
            }
        )


class AccessoriesUsedFreeRelatedObjectsManager(
    AccessoriesUsedFreeManager
):
    pass


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

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects_used_free = AccessoriesUsedFreeManager()
    objects_used_free_with_related = AccessoriesUsedFreeRelatedObjectsManager()

    def __str__(self):
        return "{} x {} - ({})".format(
            self.number_bought,
            self.accessories_name,
            self.product_number,
        )

    @cached_property
    def autocomplete_str(self):
        return "{} ({} free) x {} - ({})".format(
            self.number_bought,
            self.free,
            self.accessories_name,
            self.product_number,
        )

    @cached_property
    def used(self):
        if not self.pk:
            return 0
        try:
            return (self.user_count or 0)
        except AttributeError:
            users_qs = self.users.through.objects.filter(accessories=self)

            def get_sum(qs):
                return qs.aggregate(sum=Sum('quantity'))['sum'] or 0
            return sum(map(get_sum, [0, users_qs]))
    used._permission_field = 'number_bought'

    @cached_property
    def free(self):
        if not self.pk:
            return 0
        return self.number_bought - self.used
    free._permission_field = 'number_bought'


@reversion.register()
class AccessoriesUser(models.Model):
    accessories = models.ForeignKey(Accessories)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='accessories'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('accessories', 'user')

    def __str__(self):
        return '{} of {} assigned to {}'.format(
            self.quantity, self.accessories, self.user,
        )
