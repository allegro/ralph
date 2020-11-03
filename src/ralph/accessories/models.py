import reversion
from dj.choices import Choices
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, Prefetch
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.admin.helpers import getattr_dunder
from ralph.assets.models import BaseObject
from ralph.back_office.models import Warehouse
from ralph.lib.mixins.fields import BaseObjectForeignKey
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.polymorphic.models import PolymorphicQuerySet
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions


_SELECT_USED_ACCESSORIES_QUERY = """
    SELECT COALESCE(SUM({assignment_table}.{quantity_column}), 0)
    FROM {assignment_table}
    WHERE {assignment_table}.{licence_id_column} = {licence_table}.{id_column}
"""


class AccessoriesUsedFreeManager(models.Manager):
    def get_queryset(self):
        """
        Use subqueries in select to calculate licences used by users and
        base objects.
        """
        # Coalesce is used here to provide default value for Sum (in other
        # case None value is returned)
        # read https://code.djangoproject.com/ticket/10929 for more info
        # about default value for Sum
        id_column = Accessories.baseobject_ptr.field.column

        user_quantity_field = Accessories.users.through._meta.get_field('quantity')
        user_accessories_field = Accessories.users.through._meta.get_field('accessories')
        user_count_query = _SELECT_USED_ACCESSORIES_QUERY.format(
            assignment_table=Accessories.users.through._meta.db_table,
            quantity_column=user_quantity_field.db_column or user_quantity_field.column,  # noqa
            licence_id_column=user_accessories_field.db_column or user_accessories_field,  # noqa
            licence_table=Accessories._meta.db_table,
            id_column=id_column,
        )

        base_object_quantity_field = Accessories.base_objects.through._meta.get_field('quantity')  # noqa
        base_object_accessories_field = Accessories.base_objects.through._meta.get_field('licence')  # noqa
        base_object_count_query = _SELECT_USED_ACCESSORIES_QUERY.format(
            assignment_table=Accessories.base_objects.through._meta.db_table,
            quantity_column=base_object_quantity_field.db_column or base_object_quantity_field.column,  # noqa
            licence_id_column=base_object_accessories_field.db_column or base_object_accessories_field.column,  # noqa
            licence_table=Accessories._meta.db_table,
            id_column=id_column,
        )

        return super().get_queryset().extra(
            select={
                'user_count': user_count_query,
                'baseobject_count': base_object_count_query,
            }
        )

ACCESSORIES_RELATED_OBJECTS_PREFETCH_RELATED = [
    'users',
    # prefetch all baseobjects related with licence; this allows to call
    # [bol.base_object for bol in licence.baseobjectlicence_set.all()]
    # without additional queries
    Prefetch(
        'baseobjectlicence_set__base_object',
        # polymorphic manager is used to get final instance of the object
        # (ex. DataCenterAsset)
        queryset=BaseObject.polymorphic_objects.all()
    )
]


class AccessoriesRelatedObjectsManager(models.Manager):
    """
    Prefetch related objects by-default
    """
    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            *ACCESSORIES_RELATED_OBJECTS_PREFETCH_RELATED
        )


class AccessoriesUsedFreeRelatedObjectsManager(
    AccessoriesUsedFreeManager, AccessoriesRelatedObjectsManager
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
    base_objects = models.ManyToManyField(
        BaseObject,
        verbose_name=_('assigned base objects'),
        through='BaseObjectAccessories',
        related_name='+',
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


    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects_used_free = AccessoriesUsedFreeManager()
    objects_with_related = AccessoriesRelatedObjectsManager()
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


@reversion.register()
class BaseObjectAccessories(models.Model):
    accessories = models.ForeignKey(Accessories)
    base_object = BaseObjectForeignKey(
        BaseObject,
        related_name='accessories',
        verbose_name=_('Asset'),
        limit_models=['back_office.BackOfficeAsset',]
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('accessories', 'base_object')

    def __str__(self):
        return '{} of {} assigned to {}'.format(
            self.quantity, self.accessories, self.base_object
        )

    def clean(self):
        bo_asset = getattr_dunder(
            self.base_object, 'asset__backofficeasset'
        )
        if (
            bo_asset and self.accessories and
            self.accessories.region_id != bo_asset.region_id
        ):
            raise ValidationError(
                _('Asset region is in a different region than Accessories.')
            )
