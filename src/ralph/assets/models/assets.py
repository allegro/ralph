# -*- coding: utf-8 -*-
import datetime
import logging

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.accounts.models import Team
from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import (
    ModelVisualizationLayout,
    ObjectModelType
)
from ralph.lib.custom_fields.models import (
    CustomFieldMeta,
    WithCustomFieldsMixin
)
from ralph.lib.mixins.fields import (
    NullableCharField,
    NullableCharFieldWithAutoStrip
)
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    PriceMixin,
    TimeStampMixin
)
from ralph.lib.permissions.models import PermByFieldMixin, PermissionsBase

logger = logging.getLogger(__name__)


class AssetHolder(
    AdminAbsoluteUrlMixin, NamedMixin.NonUnique, TimeStampMixin, models.Model
):
    pass


class BusinessSegment(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    pass


class ProfitCenter(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    description = models.TextField(blank=True)


class Environment(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    pass


class Service(
    PermByFieldMixin, AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model
):
    # Fixme: let's do service catalog replacement from that
    _allow_in_dashboard = True

    active = models.BooleanField(default=True)
    uid = NullableCharField(max_length=40, unique=True, blank=True, null=True)
    profit_center = models.ForeignKey(
        ProfitCenter, null=True, blank=True, on_delete=models.CASCADE
    )
    business_segment = models.ForeignKey(
        BusinessSegment, null=True, blank=True, on_delete=models.CASCADE
    )
    cost_center = models.CharField(max_length=100, blank=True)
    environments = models.ManyToManyField("Environment", through="ServiceEnvironment")
    business_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="services_business_owner",
        blank=True,
    )
    technical_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="services_technical_owner",
        blank=True,
    )
    support_team = models.ForeignKey(
        Team, null=True, blank=True, related_name="services", on_delete=models.CASCADE
    )

    def __str__(self):
        return "{}".format(self.name)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.filter(active=True)


class ServiceEnvironment(AdminAbsoluteUrlMixin, AutocompleteTooltipMixin, BaseObject):
    _allow_in_dashboard = True
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    autocomplete_tooltip_fields = [
        "service__business_owners",
        "service__technical_owners",
        "service__support_team",
    ]

    def __str__(self):
        return "{} - {}".format(self.service.name, self.environment.name)

    class Meta:
        unique_together = ("service", "environment")
        ordering = ("service__name", "environment__name")

    @property
    def service_name(self):
        return self.service.name

    @property
    def service_uid(self):
        return self.service.uid

    @property
    def environment_name(self):
        return self.environment.name

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.filter(service__active=True)


class ManufacturerKind(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    pass


class Manufacturer(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    _allow_in_dashboard = True
    manufacturer_kind = models.ForeignKey(
        ManufacturerKind,
        verbose_name=_("manufacturer kind"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )


AssetModelMeta = type("AssetModelMeta", (CustomFieldMeta, PermissionsBase), {})


class AssetModel(
    PermByFieldMixin,
    NamedMixin.NonUnique,
    TimeStampMixin,
    AdminAbsoluteUrlMixin,
    WithCustomFieldsMixin,
    models.Model,
    metaclass=AssetModelMeta,
):
    # TODO: should type be determined based on category?
    _allow_in_dashboard = True

    type = models.PositiveIntegerField(
        verbose_name=_("type"),
        choices=ObjectModelType(),
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, blank=True, null=True
    )
    category = TreeForeignKey(
        "Category", null=True, related_name="models", on_delete=models.CASCADE
    )
    power_consumption = models.PositiveIntegerField(
        verbose_name=_("Power consumption"),
        default=0,
    )
    height_of_device = models.FloatField(
        verbose_name=_("Height of device"),
        default=0,
        validators=[MinValueValidator(0)],
    )
    cores_count = models.PositiveIntegerField(
        verbose_name=_("Cores count"),
        default=0,
    )
    visualization_layout_front = models.PositiveIntegerField(
        verbose_name=_("visualization layout of front side"),
        choices=ModelVisualizationLayout(),
        default=ModelVisualizationLayout().na.id,
        blank=True,
    )
    visualization_layout_back = models.PositiveIntegerField(
        verbose_name=_("visualization layout of back side"),
        choices=ModelVisualizationLayout(),
        default=ModelVisualizationLayout().na.id,
        blank=True,
    )
    # Used in the visualization Data Center as is_blade
    has_parent = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("model")
        verbose_name_plural = _("models")

    def __str__(self):
        if self.category_id:
            return "[{}] {} {}".format(self.category, self.manufacturer, self.name)
        else:
            return "{} {}".format(self.manufacturer, self.name)

    def _get_layout_class(self, field):
        item = ModelVisualizationLayout.from_id(field)
        return getattr(item, "css_class", "")

    def get_front_layout_class(self):
        return self._get_layout_class(self.visualization_layout_front)

    def get_back_layout_class(self):
        return self._get_layout_class(self.visualization_layout_back)


class Category(
    AdminAbsoluteUrlMixin, MPTTModel, NamedMixin.NonUnique, TimeStampMixin, models.Model
):
    _allow_in_dashboard = True

    code = models.CharField(max_length=4, blank=True, default="")
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        on_delete=models.CASCADE,
    )
    imei_required = models.BooleanField(default=False)
    allow_deployment = models.BooleanField(default=False)
    show_buyout_date = models.BooleanField(default=False)
    default_depreciation_rate = models.DecimalField(
        blank=True,
        decimal_places=2,
        default=settings.DEFAULT_DEPRECIATION_RATE,
        help_text=_(
            "This value is in percentage."
            ' For example value: "100" means it depreciates during a year.'
            ' Value: "25" means it depreciates during 4 years, and so on... .'
        ),
        max_digits=5,
    )

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    def get_default_depreciation_rate(self, category=None):
        if category is None:
            category = self

        if category.default_depreciation_rate:
            return category.default_depreciation_rate
        elif category.parent:
            return self.get_default_depreciation_rate(category.parent)
        return 0


class AssetLastHostname(models.Model):
    prefix = models.CharField(max_length=30, db_index=True)
    counter = models.PositiveIntegerField(default=1)
    postfix = models.CharField(max_length=30, db_index=True)

    class Meta:
        unique_together = ("prefix", "postfix")

    def formatted_hostname(self, fill=5):
        return "{prefix}{counter:0{fill}}{postfix}".format(
            prefix=self.prefix,
            counter=int(self.counter),
            fill=fill,
            postfix=self.postfix,
        )

    @classmethod
    # TODO: select_for_update
    def increment_hostname(cls, prefix, postfix=""):
        obj, created = cls.objects.get_or_create(
            prefix=prefix,
            postfix=postfix,
        )
        if not created:
            # F() avoid race condition problem
            obj.counter = models.F("counter") + 1
            obj.save()
            return cls.objects.get(pk=obj.pk)
        else:
            return obj

    @classmethod
    def get_next_free_hostname(
        cls, prefix, postfix, fill=5, availability_checker=None, _counter=1
    ):
        try:
            last_hostname = cls.objects.get(prefix=prefix, postfix=postfix)
        except cls.DoesNotExist:
            last_hostname = cls(prefix=prefix, postfix=postfix, counter=0)

        last_hostname.counter += _counter
        hostname = last_hostname.formatted_hostname(fill=fill)

        if availability_checker is None or availability_checker(hostname):
            return hostname
        else:
            return cls.get_next_free_hostname(
                prefix, postfix, fill, availability_checker, _counter + 1
            )

    def __str__(self):
        return self.formatted_hostname()


class BudgetInfo(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    class Meta:
        verbose_name = _("Budget info")
        verbose_name_plural = _("Budgets info")

    def __str__(self):
        return self.name


class Asset(AdminAbsoluteUrlMixin, PriceMixin, BaseObject):
    model = models.ForeignKey(
        AssetModel, related_name="assets", on_delete=models.PROTECT
    )
    # TODO: unify hostname for DCA, VirtualServer, Cluster and CloudHost
    # (use another model?)
    hostname = NullableCharFieldWithAutoStrip(
        blank=True,
        default=None,
        max_length=255,
        null=True,
        verbose_name=_("hostname"),  # TODO: unique
    )
    sn = NullableCharField(
        blank=True,
        max_length=200,
        null=True,
        verbose_name=_("SN"),
        unique=True,
        validators=[
            RegexValidator(
                r"\s",
                _("No spaces allowed"),
                inverse_match=True,
                code="no_spaces_allowed",
            )
        ],
    )
    barcode = NullableCharField(
        blank=True,
        default=None,
        max_length=200,
        null=True,
        unique=True,
        verbose_name=_("barcode"),
        validators=[
            RegexValidator(
                r"\s",
                _("No spaces allowed"),
                inverse_match=True,
                code="no_spaces_allowed",
            )
        ],
    )
    niw = NullableCharField(
        blank=True,
        default=None,
        max_length=200,
        null=True,
        verbose_name=_("inventory number"),
    )
    required_support = models.BooleanField(default=False)

    order_no = models.CharField(
        verbose_name=_("order number"),
        blank=True,
        max_length=50,
        null=True,
    )
    invoice_no = models.CharField(
        verbose_name=_("invoice number"),
        blank=True,
        db_index=True,
        max_length=128,
        null=True,
    )
    invoice_date = models.DateField(blank=True, null=True)
    # to discuss: foreign key?
    provider = models.CharField(
        blank=True,
        max_length=100,
        null=True,
    )
    depreciation_rate = models.DecimalField(
        blank=True,
        decimal_places=2,
        default=settings.DEFAULT_DEPRECIATION_RATE,
        help_text=_(
            "This value is in percentage."
            ' For example value: "100" means it depreciates during a year.'
            ' Value: "25" means it depreciates during 4 years, and so on... .'
        ),
        max_digits=5,
    )
    force_depreciation = models.BooleanField(
        help_text=("Check if you no longer want to bill for this asset"),
        default=False,
    )
    depreciation_end_date = models.DateField(blank=True, null=True)
    buyout_date = models.DateField(blank=True, null=True, db_index=True)
    task_url = models.URLField(
        blank=True,
        help_text=("External workflow system URL"),
        max_length=2048,
        null=True,
    )
    budget_info = models.ForeignKey(
        BudgetInfo,
        blank=True,
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )
    property_of = models.ForeignKey(
        AssetHolder,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    start_usage = models.DateField(
        blank=True,
        null=True,
        help_text=("Fill it if date of first usage is different then date of creation"),
    )

    def __str__(self):
        return self.hostname or ""

    def calculate_buyout_date(self):
        """
        Get buyout date.

        Calculate buyout date:
         invoice_date + buyout months offset by category

        Returns:
            Buyout date
        """
        if (
            not self.model
            or not self.model.category
            or not self.model.category.show_buyout_date
        ):
            return None

        category = self.model.category  # type: Category
        months = settings.ASSET_BUYOUT_CATEGORY_TO_MONTHS.get(str(category.pk), None)
        if self.invoice_date and months:
            return self.invoice_date + relativedelta(months=months)
        else:
            return None

    def get_depreciation_months(self):
        return int(
            (1 / (self.depreciation_rate / 100) * 12) if self.depreciation_rate else 0
        )

    def is_depreciated(self, date=None):
        date = date or datetime.date.today()
        if self.force_depreciation or not self.invoice_date:
            return True
        if self.depreciation_end_date:
            deprecation_date = self.deprecation_end_date
        else:
            deprecation_date = self.invoice_date + relativedelta(
                months=self.get_depreciation_months(),
            )
        return deprecation_date < date

    def get_depreciated_months(self):
        # DEPRECATED
        # BACKWARD_COMPATIBILITY
        return self.get_depreciation_months()

    def is_deprecated(self, date=None):
        # DEPRECATED
        # BACKWARD_COMPATIBILITY
        return self.is_depreciated()

    def _liquidated_at(self, date):
        liquidated_history = (
            self.get_history()
            .filter(
                new_value="liquidated",
                field_name="status",
            )
            .order_by("-date")[:1]
        )
        return liquidated_history and liquidated_history[0].date.date() <= date

    def clean(self):
        errors = {}
        if not self.sn and not self.barcode:
            error_message = [_("SN or BARCODE field is required")]
            errors.update({"sn": error_message, "barcode": error_message})
        if not self.property_of:
            error_message = [_("Property of field is required")]
            errors.update(
                {
                    "__all__": error_message,
                }
            )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # if you save barcode as empty string (instead of None) you could have
        # only one asset with empty barcode (because of `unique` constraint)
        # if you save barcode as None you could have many assets with empty
        # barcode (becasue `unique` constrainst is skipped)
        for unique_field in ["barcode", "sn"]:
            value = getattr(self, unique_field, None)
            if value == "":
                value = None
            setattr(self, unique_field, value)

        if not self.buyout_date:
            self.buyout_date = self.calculate_buyout_date()
        return super(Asset, self).save(*args, **kwargs)
