# -*- coding: utf-8 -*-
import datetime

from dateutil.relativedelta import relativedelta
from dj.choices import Country
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.accounts.models import Team
from ralph.assets.country_utils import iso2_to_iso3
from ralph.assets.models.base import BaseObject
from ralph.assets.models.choices import (
    ModelVisualizationLayout,
    ObjectModelType
)
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.permissions import PermByFieldMixin

ASSET_HOSTNAME_TEMPLATE = getattr(settings, 'ASSET_HOSTNAME_TEMPLATE', None)
if not ASSET_HOSTNAME_TEMPLATE:
    raise ImproperlyConfigured('"ASSET_HOSTNAME_TEMPLATE" must be specified.')


def get_user_iso3_country_name(user):
    """
    :param user: instance of django.contrib.auth.models.User which has profile
        with country attribute
    """
    country_name = Country.name_from_id(int(user.country))
    iso3_country_name = iso2_to_iso3(country_name)
    return iso3_country_name


class BusinessSegment(NamedMixin, models.Model):
    pass


class ProfitCenter(NamedMixin, models.Model):
    business_segment = models.ForeignKey(BusinessSegment)
    description = models.TextField(blank=True)


class Environment(NamedMixin, TimeStampMixin, models.Model):
    pass


class Service(NamedMixin, TimeStampMixin, models.Model):
    # Fixme: let's do service catalog replacement from that
    active = models.BooleanField(default=True)
    uid = NullableCharField(max_length=40, unique=True, blank=True, null=True)
    profit_center = models.ForeignKey(ProfitCenter, null=True, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    environments = models.ManyToManyField(
        'Environment', through='ServiceEnvironment'
    )
    business_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='services_business_owner',
        blank=True,
    )
    technical_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='services_technical_owner',
        blank=True,
    )
    support_team = models.ForeignKey(
        Team, null=True, blank=True, related_name='services',
    )

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('assets:service_detail', args=(self.pk,))


class ServiceEnvironment(models.Model):
    service = models.ForeignKey(Service)
    environment = models.ForeignKey(Environment)

    def __str__(self):
        return '{} - {}'.format(self.service.name, self.environment.name)

    class Meta:
        unique_together = ('service', 'environment')


class Manufacturer(NamedMixin, TimeStampMixin, models.Model):
    pass


class AssetModel(
    PermByFieldMixin,
    NamedMixin.NonUnique,
    TimeStampMixin,
    models.Model
):
    # TODO: should type be determined based on category?
    type = models.PositiveIntegerField(
        verbose_name=_('type'), choices=ObjectModelType(),
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, blank=True, null=True
    )
    category = TreeForeignKey(
        'Category', null=True, related_name='models'
    )
    power_consumption = models.IntegerField(
        verbose_name=_("Power consumption"),
        blank=True,
        default=0,
    )
    height_of_device = models.FloatField(
        verbose_name=_("Height of device"),
        blank=True,
        default=0,
    )
    cores_count = models.IntegerField(
        verbose_name=_("Cores count"),
        blank=True,
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
        verbose_name = _('model')
        verbose_name_plural = _('models')

    def __str__(self):
        if self.category:
            return '[{}] {} {}'.format(
                self.category, self.manufacturer, self.name
            )
        else:
            return '{} {}'.format(
                self.manufacturer, self.name
            )

    def _get_layout_class(self, field):
        item = ModelVisualizationLayout.from_id(field)
        return getattr(item, 'css_class', '')

    def get_front_layout_class(self):
        return self._get_layout_class(self.visualization_layout_front)

    def get_back_layout_class(self):
        return self._get_layout_class(self.visualization_layout_back)


class Category(MPTTModel, NamedMixin.NonUnique, TimeStampMixin, models.Model):
    code = models.CharField(max_length=4, blank=True, default='')
    parent = TreeForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        db_index=True
    )
    imei_required = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name


class AssetLastHostname(models.Model):
    prefix = models.CharField(max_length=8, db_index=True)
    counter = models.PositiveIntegerField(default=1)
    postfix = models.CharField(max_length=8, db_index=True)

    class Meta:
        unique_together = ('prefix', 'postfix')

    def formatted_hostname(self, fill=5):
        return '{prefix}{counter:0{fill}}{postfix}'.format(
            prefix=self.prefix,
            counter=int(self.counter),
            fill=fill,
            postfix=self.postfix,
        )

    @classmethod
    def increment_hostname(cls, prefix, postfix=''):
        obj, created = cls.objects.get_or_create(
            prefix=prefix,
            postfix=postfix,
        )
        if not created:
            # F() avoid race condition problem
            obj.counter = models.F('counter') + 1
            obj.save()
            return cls.objects.get(pk=obj.pk)
        else:
            return obj

    def __str__(self):
        return self.formatted_hostname()


class Asset(AdminAbsoluteUrlMixin, BaseObject):
    model = models.ForeignKey(AssetModel, related_name='assets')
    hostname = models.CharField(
        blank=True,
        default=None,
        max_length=255,
        null=True,
        verbose_name=_('hostname'),
    )
    sn = NullableCharField(
        blank=True,
        max_length=200,
        null=True,
        verbose_name=_('SN'),
        unique=True,
    )
    barcode = NullableCharField(
        blank=True,
        default=None,
        max_length=200,
        null=True,
        unique=True,
        verbose_name=_('barcode')
    )
    niw = NullableCharField(
        blank=True,
        default=None,
        max_length=200,
        null=True,
        verbose_name=_('Inventory number'),
    )
    required_support = models.BooleanField(default=False)

    order_no = models.CharField(
        blank=True,
        max_length=50,
        null=True,
    )
    invoice_no = models.CharField(
        blank=True,
        db_index=True,
        max_length=128,
        null=True,
    )
    invoice_date = models.DateField(blank=True, null=True)
    price = models.DecimalField(
        blank=True,
        decimal_places=2,
        default=0,
        max_digits=10,
        null=True,
    )
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
            'This value is in percentage.'
            ' For example value: "100" means it depreciates during a year.'
            ' Value: "25" means it depreciates during 4 years, and so on... .'
        ),
        max_digits=5,
    )
    force_depreciation = models.BooleanField(
        help_text=(
            'Check if you no longer want to bill for this asset'
        ),
    )
    depreciation_end_date = models.DateField(blank=True, null=True)
    task_url = models.URLField(
        blank=True,
        help_text=('External workflow system URL'),
        max_length=2048,
        null=True,
    )

    def __str__(self):
        return self.hostname

    def get_deprecation_months(self):
        return int(
            (1 / (self.depreciation_rate / 100) * 12)
            if self.depreciation_rate else 0
        )

    def is_depreciated(self, date=None):
        date = date or datetime.date.today()
        if self.force_depreciation or not self.invoice_date:
            return True
        if self.depreciation_end_date:
            deprecation_date = self.deprecation_end_date
        else:
            deprecation_date = self.invoice_date + relativedelta(
                months=self.get_deprecation_months(),
            )
        return deprecation_date < date

    def get_depreciated_months(self):
        # DEPRECATED
        # BACKWARD_COMPATIBILITY
        return self.get_deprecation_months()

    def is_deprecated(self, date=None):
        # DEPRECATED
        # BACKWARD_COMPATIBILITY
        return self.is_depreciated()

    def generate_hostname(self, commit=True, template_vars=None):
        def render_template(template):
            template = Template(template)
            context = Context(template_vars or {})
            return template.render(context)
        prefix = render_template(
            ASSET_HOSTNAME_TEMPLATE.get('prefix', ''),
        )
        postfix = render_template(
            ASSET_HOSTNAME_TEMPLATE.get('postfix', ''),
        )
        counter_length = ASSET_HOSTNAME_TEMPLATE.get('counter_length', 5)
        last_hostname = AssetLastHostname.increment_hostname(prefix, postfix)
        self.hostname = last_hostname.formatted_hostname(fill=counter_length)
        if commit:
            self.save()

    def _try_assign_hostname(self, commit):
        if self.owner and self.model.category and self.model.category.code:
            template_vars = {
                'code': self.model.category.code,
                'country_code': self.country_code,
            }
            if not self.hostname:
                self.generate_hostname(commit, template_vars)
            else:
                user_country = get_user_iso3_country_name(self.owner)
                different_country = user_country not in self.hostname
                if different_country:
                    self.generate_hostname(commit, template_vars)

    def _liquidated_at(self, date):
        liquidated_history = self.get_history().filter(
            new_value='liquidated',
            field_name='status',
        ).order_by('-date')[:1]
        return liquidated_history and liquidated_history[0].date.date() <= date

    def clean(self):
        if not self.sn and not self.barcode:
            error_message = [_('SN or BARCODE field is required')]
            raise ValidationError(
                {
                    'sn': error_message,
                    'barcode': error_message
                }
            )

    def save(self, *args, **kwargs):
        # if you save barcode as empty string (instead of None) you could have
        # only one asset with empty barcode (because of `unique` constraint)
        # if you save barcode as None you could have many assets with empty
        # barcode (becasue `unique` constrainst is skipped)
        for unique_field in ['barcode', 'sn']:
            value = getattr(self, unique_field, None)
            if value == '':
                value = None
            setattr(self, unique_field, value)
        return super(Asset, self).save(*args, **kwargs)
