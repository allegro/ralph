# -*- coding: utf-8 -*-
"""SAM module models."""
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.models.assets import Manufacturer
from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.permissions import PermByFieldMixin


class LicenceType(PermByFieldMixin, NamedMixin, models.Model):

    """The type of a licence"""

    @classmethod
    def create_from_string(cls, string_name, *args, **kwargs):
        return cls(name=string_name)


class SoftwareCategory(PermByFieldMixin, NamedMixin, models.Model):

    """The category of the licensed software"""

    # asset_type = models.PositiveSmallIntegerField(
    #     choices=AssetType()
    # )

    @classmethod
    def create_from_string(cls, asset_type, string_name):
        return cls(asset_type=asset_type, name=string_name)

    @property
    def licences(self):
        """Iterate over licences."""
        for licence in self.licences.all():
            yield licence

    class Meta:
        verbose_name_plural = _('software categories')


class Licence(
    Regionalizable,
    AdminAbsoluteUrlMixin,
    PermByFieldMixin,
    TimeStampMixin,
    models.Model,
):

    """A set of licences for a single software with a single expiration date"""

    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    licence_type = models.ForeignKey(
        LicenceType,
        on_delete=models.PROTECT,
        help_text=_(
            "Should be like 'per processor' or 'per machine' and so on. ",
        ),
    )
    # property_of = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.PROTECT,
    #     null=True,
    # )
    software_category = models.ForeignKey(
        SoftwareCategory,
        on_delete=models.PROTECT,
    )
    number_bought = models.IntegerField(
        verbose_name=_('Number of purchased items'),
    )
    sn = models.TextField(
        verbose_name=_('SN / Key'),
        null=True,
        blank=True,
    )
    niw = models.CharField(
        max_length=200,
        verbose_name=_('Inventory number'),
        null=False,
        unique=True,
        default='N/A',
    )
    invoice_date = models.DateField(
        verbose_name=_('Invoice date'),
        null=True,
        blank=True,
    )
    valid_thru = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank if this licence is perpetual",
    )
    order_no = models.CharField(max_length=50, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, null=True, blank=True,
    )
    accounting_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_(
            'Any value to help your accounting department '
            'identify this licence'
        ),
    )
    base_objects = models.ManyToManyField(
        BaseObject,
        verbose_name=_('Assigned base objects'),
        through='BaseObjectLicence',
        related_name='+',
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='LicenceUser',
        related_name='+'
    )
    provider = models.CharField(max_length=100, null=True, blank=True)
    invoice_no = models.CharField(
        max_length=128, db_index=True, null=True, blank=True
    )
    remarks = models.TextField(blank=True)
    license_details = models.CharField(
        verbose_name=_('License details'),
        max_length=1024,
        blank=True,
        default='',
    )
    # TODO. To discuss
    # parent = TreeForeignKey(
    #     'self',
    #     null=True,
    #     blank=True,
    #     related_name='children',
    #     verbose_name=_('Parent licence'),
    # )
    # TODO. To discuss
    # service_name = models.ForeignKey(Service, null=True, blank=True)
    # budget_info = models.ForeignKey(
    #     BudgetInfo,
    #     blank=True,
    #     default=None,
    #     null=True,
    #     on_delete=models.PROTECT,
    # )
    # asset_type = models.PositiveSmallIntegerField(
    #     choices=AssetType(),
    #     verbose_name=_('Type'),
    # )

    _used = None

    def __str__(self):
        return "{} x {} - {}".format(
            self.number_bought,
            self.software_category.name,
            self.invoice_date,
        )

    @cached_property
    def used(self):
        base_objects_qs = self.base_objects.through.objects.filter(
            licence=self
        )
        users_qs = self.users.through.objects.filter(licence=self)

        def get_sum(qs):
            return qs.aggregate(sum=Sum('quantity'))['sum'] or 0
        return sum(map(get_sum, [base_objects_qs, users_qs]))

    @cached_property
    def free(self):
        return self.number_bought - self.used


class BaseObjectLicence(models.Model):
    licence = models.ForeignKey(Licence)
    base_object = models.ForeignKey(BaseObject, related_name='licences')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('licence', 'base_object')

    def __str__(self):
        return '{} of {} assigned to {}'.format(
            self.quantity, self.licence, self.base_object
        )


class LicenceUser(models.Model):
    licence = models.ForeignKey(Licence)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='licences'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('licence', 'user')

    def __str__(self):
        return '{} of {} assigned to {}'.format(
            self.quantity, self.licence, self.user,
        )
