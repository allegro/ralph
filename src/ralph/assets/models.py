# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from dateutil.relativedelta import relativedelta

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.template import Context, Template

from dj.choices import Choices

try:
    from django.utils.timezone import now as datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now

ASSET_HOSTNAME_TEMPLATE = getattr(settings, 'ASSET_HOSTNAME_TEMPLATE', None)
if not ASSET_HOSTNAME_TEMPLATE:
    raise ImproperlyConfigured('"ASSET_HOSTNAME_TEMPLATE" must be specified.')


from ralph.assets.overrides import Country


def _replace_empty_with_none(obj, fields):
    # XXX: replace '' with None, because null=True on model doesn't work
    for field in fields:
        value = getattr(obj, field, None)
        if value == '':
            setattr(obj, field, None)


def get_user_iso3_country_name(user):
    """
    :param user: instance of django.contrib.auth.models.User which has profile
        with country attribute
    """
    country_name = Country.name_from_id(user.get_profile().country)
    iso3_country_name = Country.iso2_to_iso3(country_name)
    return iso3_country_name


# old: Named
@python_2_unicode_compatible
class NamedMixin(models.Model):
    """Describes an abstract model with a unique ``name`` field."""
    name = models.CharField(_('name'), max_length=50, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @python_2_unicode_compatible
    class NonUnique(models.Model):
        """Describes an abstract model with a non-unique ``name`` field."""
        name = models.CharField(verbose_name=_("name"), max_length=75)

        class Meta:
            abstract = True

        def __str__(self):
            return self.name


# old: TimeTrackable
class TimeStampMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('date created'),
        auto_now=True,
    )
    modified = models.DateTimeField(
        verbose_name=_('last modified'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ('-modified', '-created',)


class Environment(NamedMixin, TimeStampMixin, models.Model):
    pass


@python_2_unicode_compatible
class Service(NamedMixin, TimeStampMixin, models.Model):
    # Fixme: let's do service catalog replacement from that
    profit_center = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    environments = models.ManyToManyField(
        'Environment', through='ServiceEnvironment'
    )

    def __str__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('assets:service_detail', args=(self.pk,))


class ServiceEnvironment(models.Model):
    service = models.ForeignKey(Service)
    environment = models.ForeignKey(Environment)


class LicenseType(Choices):
    _ = Choices.Choice
    not_applicable = _('not applicable')
    oem = _('oem')
    box = _('box')


class AssetPurpose(Choices):
    _ = Choices.Choice

    for_contractor = _("for contractor")
    sectional = _("sectional")
    for_dashboards = _("for dashboards")
    for_events = _("for events")
    for_tests = _("for tests")
    others = _("others")


class AssetStatus(Choices):
    _ = Choices.Choice

    HARDWARE = Choices.Group(0)
    new = _('new')
    in_progress = _('in progress')
    waiting_for_release = _('waiting for release')
    used = _('in use')
    loan = _('loan')
    damaged = _('damaged')
    liquidated = _('liquidated')
    in_service = _('in service')
    in_repair = _('in repair')
    ok = _('ok')
    to_deploy = _('to deploy')


class AssetSource(Choices):
    _ = Choices.Choice

    shipment = _('shipment')
    salvaged = _('salvaged')


class ObjectModelType(Choices):
    _ = Choices.Choice

    back_office = _('back office')
    data_center = _('data center')
    part = _('part')
    all = _('all')


class ModelVisualizationLayout(Choices):
    _ = Choices.Choice

    na = _('N/A')
    layout_1x2 = _('1x2').extra(css_class='rows-1 cols-2')
    layout_2x8 = _('2x8').extra(css_class='rows-2 cols-8')
    layout_2x8AB = _('2x16 (A/B)').extra(css_class='rows-2 cols-8 half-slots')
    layout_4x2 = _('4x2').extra(css_class='rows-4 cols-2')


class Manufacturer(NamedMixin, TimeStampMixin, models.Model):
    pass


@python_2_unicode_compatible
class AssetModel(NamedMixin.NonUnique, TimeStampMixin, models.Model):
    type = models.PositiveIntegerField(
        verbose_name=_('type'), choices=ObjectModelType(),
    )
    manufacturer = models.ForeignKey(
        Manufacturer, on_delete=models.PROTECT, blank=True, null=True
    )
    category = models.ForeignKey(
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

    class Meta:
        verbose_name = _('model')
        verbose_name_plural = _('models')

    def __str__(self):
        return '%s %s' % (self.manufacturer, self.name)

    def _get_layout_class(self, field):
        item = ModelVisualizationLayout.from_id(field)
        return getattr(item, 'css_class', '')

    def get_front_layout_class(self):
        return self._get_layout_class(self.visualization_layout_front)

    def get_back_layout_class(self):
        return self._get_layout_class(self.visualization_layout_back)


@python_2_unicode_compatible
class Category(NamedMixin.NonUnique, TimeStampMixin, models.Model):
    code = models.CharField(max_length=4, blank=True, default='')
    is_blade = models.BooleanField()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __str__(self):
        return self.name


@python_2_unicode_compatible
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


class Asset(TimeStampMixin, models.Model):
    remarks = models.TextField()
    parent = models.ForeignKey('self')
    service_env = models.ForeignKey(ServiceEnvironment)
    model = models.ForeignKey(AssetModel)
    # or hostname
    name = models.CharField(
        blank=True,
        default=None,
        max_length=16,
        null=True,
        unique=True,
    )


class BasePhysicalAsset(models.Model):
    niw = models.CharField(
        max_length=200, null=True, blank=True, default=None,
        verbose_name=_('Inventory number'),
    )
    invoice_no = models.CharField(
        max_length=128, db_index=True, null=True, blank=True,
    )
    required_support = models.BooleanField(default=False)
    order_no = models.CharField(max_length=50, null=True, blank=True)
    purchase_order = models.CharField(max_length=50, null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    sn = models.CharField(max_length=200, null=True, blank=True, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True, default=None,
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True, null=True,
    )
    # to discuss: foreign key?
    provider = models.CharField(max_length=100, null=True, blank=True)
    source = models.PositiveIntegerField(
        verbose_name=_("source"), choices=AssetSource(), db_index=True,
        null=True, blank=True,
    )
    status = models.PositiveSmallIntegerField(
        default=AssetStatus.new.id,
        verbose_name=_("status"),
        choices=AssetStatus(),
        null=True,
        blank=True,
    )
    request_date = models.DateField(null=True, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    production_use_date = models.DateField(null=True, blank=True)
    provider_order_date = models.DateField(null=True, blank=True)
    deprecation_rate = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        blank=True,
        default=settings.DEFAULT_DEPRECATION_RATE,
        help_text=_(
            'This value is in percentage.'
            ' For example value: "100" means it depreciates during a year.'
            ' Value: "25" means it depreciates during 4 years, and so on... .'
        ),
    )
    force_deprecation = models.BooleanField(help_text=(
        'Check if you no longer want to bill for this asset'
    ))
    deprecation_end_date = models.DateField(null=True, blank=True)
    production_year = models.PositiveSmallIntegerField(null=True, blank=True)
    task_url = models.URLField(
        max_length=2048, null=True, blank=True, unique=False,
        help_text=('External workflow system URL'),
    )
    loan_end_date = models.DateField(
        null=True, blank=True, default=None, verbose_name=_('Loan end date'),
    )

    class Meta:
        abstract = True

    def get_deprecation_months(self):
        return int(
            (1 / (self.deprecation_rate / 100) * 12)
            if self.deprecation_rate else 0
        )

    def is_depreciated(self, date=None):
        date = date or datetime.date.today()
        if self.force_deprecation or not self.invoice_date:
            return True
        if self.deprecation_end_date:
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

    def generate_hostname(self, commit=True, template_vars={}):
        def render_template(template):
            template = Template(template)
            context = Context(template_vars)
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

    def is_liquidated(self, date=None):
        date = date or datetime.date.today()
        # check if asset has status 'liquidated' and if yes, check if it has
        # this status on given date
        if self.status == AssetStatus.liquidated and self._liquidated_at(date):
            return True
        return False

    def _liquidated_at(self, date):
        liquidated_history = self.get_history().filter(
            new_value='liquidated',
            field_name='status',
        ).order_by('-date')[:1]
        return liquidated_history and liquidated_history[0].date.date() <= date


# COMPONENTS
class ComponentType(Choices):
    _ = Choices.Choice

    processor = _('processor')
    memory = _('memory')
    disk = _('disk drive')
    ethernet = _('ethernet card')
    expansion = _('expansion card')
    fibre = _('fibre channel card')
    share = _('disk share')
    unknown = _('unknown')
    management = _('management')
    power = _('power module')
    cooling = _('cooling device')
    media = _('media tray')
    chassis = _('chassis')
    backup = _('backup')
    software = _('software')
    os = _('operating system')


@python_2_unicode_compatible
class ComponentModel(NamedMixin, models.Model):
    speed = models.PositiveIntegerField(
        verbose_name=_('speed (MHz)'),
        default=0,
        blank=True,
    )
    cores = models.PositiveIntegerField(
        verbose_name=_('number of cores'),
        default=0,
        blank=True,
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'),
        default=0,
        blank=True,
    )
    type = models.PositiveIntegerField(
        verbose_name=_('component type'),
        choices=ComponentType(),
        default=ComponentType.unknown.id,
    )
    family = models.CharField(blank=True, default='', max_length=128)

    class Meta:
        unique_together = ('speed', 'cores', 'size', 'type', 'family')
        verbose_name = _('component model')
        verbose_name_plural = _('component models')

    def __str__(self):
        return self.name


class Component(models.Model):
    asset = models.ForeignKey(Asset, related_name='%(class)s')
    model = models.ForeignKey(
        ComponentModel,
        verbose_name=_('model'),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True


class GenericComponent(Component):
    label = models.CharField(
        verbose_name=_('label'), max_length=255, blank=True,
        null=True, default=None,
    )
    sn = models.CharField(
        verbose_name=_('vendor SN'), max_length=255, unique=True, null=True,
        blank=True, default=None,
    )

    class Meta:
        verbose_name = _('generic component')
        verbose_name_plural = _('generic components')
