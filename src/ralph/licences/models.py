# -*- coding: utf-8 -*-
"""SAM module models."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Prefetch, Sum
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from reversion import revisions as reversion

from ralph.accounts.models import Regionalizable
from ralph.admin.helpers import getattr_dunder
from ralph.assets.models.assets import AssetHolder, BudgetInfo, Manufacturer
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import ObjectModelType
from ralph.lib.mixins.fields import BaseObjectForeignKey
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    PriceMixin
)
from ralph.lib.permissions.models import PermByFieldMixin
from ralph.lib.polymorphic.models import PolymorphicQuerySet


_SELECT_USED_LICENCES_QUERY = """
    SELECT COALESCE(SUM({assignment_table}.{quantity_column}), 0)
    FROM {assignment_table}
    WHERE {assignment_table}.{licence_id_column} = {licence_table}.{id_column}
"""


class LicenceType(AdminAbsoluteUrlMixin, PermByFieldMixin, NamedMixin, models.Model):
    """The type of a licence"""

    @classmethod
    def create_from_string(cls, string_name, *args, **kwargs):
        return cls(name=string_name)


class Software(AdminAbsoluteUrlMixin, PermByFieldMixin, NamedMixin, models.Model):
    """The category of the licensed software"""

    _allow_in_dashboard = True

    asset_type = models.PositiveSmallIntegerField(
        choices=ObjectModelType(), default=ObjectModelType.all.id
    )

    @classmethod
    def create_from_string(cls, asset_type, string_name):
        return cls(asset_type=asset_type, name=string_name)

    @property
    def licences(self):
        """Iterate over licences."""
        for licence in self.licences.all():
            yield licence

    class Meta:
        verbose_name_plural = _("software categories")


class LicencesUsedFreeManager(models.Manager):
    def get_queryset(self):
        """
        Use subqueries in select to calculate licences used by users and
        base objects.
        """
        # Coalesce is used here to provide default value for Sum (in other
        # case None value is returned)
        # read https://code.djangoproject.com/ticket/10929 for more info
        # about default value for Sum
        id_column = Licence.baseobject_ptr.field.column

        user_quantity_field = Licence.users.through._meta.get_field("quantity")
        user_licence_field = Licence.users.through._meta.get_field("licence")
        user_count_query = _SELECT_USED_LICENCES_QUERY.format(
            assignment_table=Licence.users.through._meta.db_table,
            quantity_column=user_quantity_field.db_column or user_quantity_field.column,  # noqa
            licence_id_column=user_licence_field.db_column or user_licence_field.column,  # noqa
            licence_table=Licence._meta.db_table,
            id_column=id_column,
        )

        base_object_quantity_field = Licence.base_objects.through._meta.get_field(
            "quantity"
        )  # noqa
        base_object_licence_field = Licence.base_objects.through._meta.get_field(
            "licence"
        )  # noqa
        base_object_count_query = _SELECT_USED_LICENCES_QUERY.format(
            assignment_table=Licence.base_objects.through._meta.db_table,
            quantity_column=base_object_quantity_field.db_column
            or base_object_quantity_field.column,  # noqa
            licence_id_column=base_object_licence_field.db_column
            or base_object_licence_field.column,  # noqa
            licence_table=Licence._meta.db_table,
            id_column=id_column,
        )

        return (
            super()
            .get_queryset()
            .extra(
                select={
                    "user_count": user_count_query,
                    "baseobject_count": base_object_count_query,
                }
            )
        )


LICENCES_RELATED_OBJECTS_PREFETCH_RELATED = [
    "users",
    # prefetch all baseobjects related with licence; this allows to call
    # [bol.base_object for bol in licence.baseobjectlicence_set.all()]
    # without additional queries
    Prefetch(
        "baseobjectlicence_set__base_object",
        # polymorphic manager is used to get final instance of the object
        # (ex. DataCenterAsset)
        queryset=BaseObject.polymorphic_objects.all(),
    ),
]


class LicencesRelatedObjectsManager(models.Manager):
    """
    Prefetch related objects by-default
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(*LICENCES_RELATED_OBJECTS_PREFETCH_RELATED)
        )


class LicencesUsedFreeRelatedObjectsManager(
    LicencesUsedFreeManager, LicencesRelatedObjectsManager
):
    pass


class Licence(Regionalizable, AdminAbsoluteUrlMixin, PriceMixin, BaseObject):
    """A set of licences for a single software with a single expiration date"""

    _allow_in_dashboard = True

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
    property_of = models.ForeignKey(
        AssetHolder,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    software = models.ForeignKey(
        Software,
        on_delete=models.PROTECT,
    )
    number_bought = models.IntegerField(
        verbose_name=_("number of purchased items"),
    )
    sn = models.TextField(
        verbose_name=_("SN / key"),
        null=True,
        blank=True,
    )
    niw = models.CharField(
        max_length=200,
        verbose_name=_("inventory number"),
        null=False,
        unique=True,
        default="N/A",
    )
    invoice_date = models.DateField(
        verbose_name=_("invoice date"),
        null=True,
        blank=True,
    )
    valid_thru = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank if this licence is perpetual",
    )
    order_no = models.CharField(max_length=50, null=True, blank=True)

    depreciation_rate = models.DecimalField(
        blank=True,
        null=True,
        decimal_places=2,
        default=settings.DEFAULT_LICENCE_DEPRECIATION_RATE,
        help_text=_(
            "This value is in percentage."
            ' For example value: "100" means it depreciates during a year.'
            ' Value: "25" means it depreciates during 4 years, and so on... .'
        ),
        max_digits=5,
    )
    accounting_id = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_(
            "Any value to help your accounting department " "identify this licence"
        ),
    )
    base_objects = models.ManyToManyField(
        BaseObject,
        verbose_name=_("assigned base objects"),
        through="BaseObjectLicence",
        related_name="+",
    )
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="LicenceUser", related_name="+"
    )
    provider = models.CharField(max_length=100, null=True, blank=True)
    invoice_no = models.CharField(max_length=128, db_index=True, null=True, blank=True)
    license_details = models.CharField(
        verbose_name=_("license details"),
        max_length=1024,
        blank=True,
        default="",
    )
    office_infrastructure = models.ForeignKey(
        "back_office.OfficeInfrastructure",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    budget_info = models.ForeignKey(
        BudgetInfo,
        blank=True,
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )
    start_usage = models.DateField(
        blank=True,
        null=True,
        help_text=("Fill it if date of first usage is different then date of creation"),
    )

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects_used_free = LicencesUsedFreeManager()
    objects_with_related = LicencesRelatedObjectsManager()
    objects_used_free_with_related = LicencesUsedFreeRelatedObjectsManager()

    def __str__(self):
        return "{} x {} - {} ({})".format(
            self.number_bought,
            self.software.name,
            self.invoice_date,
            self.niw,
        )

    @cached_property
    def autocomplete_str(self):
        return "{} ({} free) x {} - {} ({})".format(
            self.number_bought,
            self.free,
            self.software.name,
            self.invoice_date,
            self.niw,
        )

    @cached_property
    def used(self):
        if not self.pk:
            return 0
        try:
            # try use fields from objects_used_free manager
            return (self.user_count or 0) + (self.baseobject_count or 0)
        except AttributeError:
            base_objects_qs = self.base_objects.through.objects.filter(licence=self)
            users_qs = self.users.through.objects.filter(licence=self)

            def get_sum(qs):
                return qs.aggregate(sum=Sum("quantity"))["sum"] or 0

            return sum(map(get_sum, [base_objects_qs, users_qs]))

    used._permission_field = "number_bought"

    @cached_property
    def free(self):
        if not self.pk:
            return 0
        return self.number_bought - self.used

    free._permission_field = "number_bought"

    @classmethod
    def get_autocomplete_queryset(cls):
        # filter by ids of licences which could be assigned (are not fully
        # used)
        return cls.objects_used_free.filter(
            pk__in=[l.id for l in cls.objects_used_free.all() if l.free > 0]
        )


@reversion.register()
class BaseObjectLicence(models.Model):
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE)
    base_object = BaseObjectForeignKey(
        BaseObject,
        related_name="licences",
        verbose_name=_("Asset"),
        limit_models=[
            "back_office.BackOfficeAsset",
            "data_center.DataCenterAsset",
            "virtual.VirtualServer",
            "data_center.Cluster",
        ],
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("licence", "base_object")

    def __str__(self):
        return "{} of {} assigned to {}".format(
            self.quantity, self.licence, self.base_object
        )

    def clean(self):
        bo_asset = getattr_dunder(self.base_object, "asset__backofficeasset")
        if bo_asset and self.licence and self.licence.region_id != bo_asset.region_id:
            raise ValidationError(
                _("Asset region is in a different region than licence.")
            )


class LicenceUser(models.Model):
    licence = models.ForeignKey(Licence, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="licences", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("licence", "user")

    def __str__(self):
        return "{} of {} assigned to {}".format(
            self.quantity,
            self.licence,
            self.user,
        )
