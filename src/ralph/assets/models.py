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


class Orientation(Choices):
    _ = Choices.Choice

    DEPTH = Choices.Group(0)
    front = _("front")
    back = _("back")
    middle = _("middle")

    WIDTH = Choices.Group(100)
    left = _("left")
    right = _("right")

    @classmethod
    def is_width(cls, orientation):
        is_width = orientation in set(
            [choice.id for choice in cls.WIDTH.choices]
        )
        return is_width

    @classmethod
    def is_depth(cls, orientation):
        is_depth = orientation in set(
            [choice.id for choice in cls.DEPTH.choices]
        )
        return is_depth


# old: Named
class NamedMixin(models.Model):
    """Describes an abstract model with a unique ``name`` field."""
    name = models.CharField(_('name'), max_length=50, unique=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    class NonUnique(models.Model):
        """Describes an abstract model with a non-unique ``name`` field."""
        name = models.CharField(verbose_name=_("name"), max_length=75)

        class Meta:
            abstract = True

        def __unicode__(self):
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


class Service(NamedMixin, TimeStampMixin, models.Model):
    # Fixme: let's do service catalog replacement from that
    profit_center = models.CharField(max_length=100, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    environments = models.ManyToManyField(
        'Environment', through='ServiceEnvironment'
    )

    def __unicode__(self):
        return '{}'.format(self.name)

    def get_absolute_url(self):
        return reverse('assets:service_detail', args=(self.pk,))


class Environment(NamedMixin, TimeStampMixin, models.Model):
    pass


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

    # SOFTWARE = Choices.Group(100)
    # installed = _('installed')
    # free = _('free')
    # reserved = _('reserved')


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


class DataCenter(NamedMixin, models.Model):

    visualization_cols_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid columns number'),
        default=20,
    )
    visualization_rows_num = models.PositiveIntegerField(
        verbose_name=_('visualization grid rows number'),
        default=20,
    )

    def __unicode__(self):
        return self.name


class ServerRoom(NamedMixin.NonUnique, models.Model):
    data_center = models.ForeignKey(DataCenter, verbose_name=_("data center"))

    def __unicode__(self):
        return '{} ({})'.format(self.name, self.data_center.name)


class RackOrientation(Choices):
    _ = Choices.Choice

    top = _("top")
    bottom = _("bottom")
    left = _("left")
    right = _("right")


class Accessory(NamedMixin):

    class Meta:
        verbose_name = _('accessory')
        verbose_name_plural = _('accessories')


class RackAccessory(models.Model):
    accessory = models.ForeignKey(Accessory)
    rack = models.ForeignKey('Rack')
    # data_center = models.ForeignKey(DataCenter, null=True, blank=False)
    # server_room = models.ForeignKey(ServerRoom, null=True, blank=False)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )
    position = models.IntegerField(null=True, blank=False)
    remarks = models.CharField(
        verbose_name='Additional remarks',
        max_length=1024,
        blank=True,
    )

    def get_orientation_desc(self):
        return Orientation.name_from_id(self.orientation)

    def __unicode__(self):
        rack_name = self.rack.name if self.rack else ''
        accessory_name = self.accessory.name if self.accessory else ''
        return 'RackAccessory: {rack_name} - {accessory_name}'.format(
            rack_name=rack_name, accessory_name=accessory_name,
        )


class Rack(NamedMixin.NonUnique, models.Model):
    class Meta:
        unique_together = ('name', 'server_room')

    server_room = models.ForeignKey(
        ServerRoom, verbose_name=_('server room'),
        null=True,
        blank=True,
    )
    description = models.CharField(
        _('description'), max_length=250, blank=True
    )
    orientation = models.PositiveIntegerField(
        choices=RackOrientation(),
        default=RackOrientation.top.id,
    )
    max_u_height = models.IntegerField(default=48)

    visualization_col = models.PositiveIntegerField(
        verbose_name=_('column number on visualization grid'),
        default=0,
    )
    visualization_row = models.PositiveIntegerField(
        verbose_name=_('row number on visualization grid'),
        default=0,
    )
    accessories = models.ManyToManyField(Accessory, through='RackAccessory')

    # def get_free_u(self):
    #     assets = self.get_root_assets()
    #     assets_height = assets.aggregate(
    #         sum=Sum('model__height_of_device'))['sum'] or 0
    #     # accesory always has 1U of height
    #     accessories = RackAccessory.objects.values_list(
    #         'position', flat=True).filter(rack=self)
    #     return self.max_u_height - assets_height - len(set(accessories))

    # def get_orientation_desc(self):
    #     return RackOrientation.name_from_id(self.orientation)

    # def get_pdus(self):
    #     from ralph_assets.models_assets import Asset
    #     return Asset.objects.select_related('model', 'device_info').filter(
    #         device_info__rack=self,
    #         device_info__orientation__in=(Orientation.left, Orientation.right),
    #         device_info__position=0,
    #     )

    # def get_root_assets(self, side=None):
    #     # FIXME: don't know what this function does.
    #     from ralph_assets.models_assets import Asset
    #     filter_kwargs = {
    #         'device_info__rack': self,
    #         'device_info__slot_no': '',
    #     }
    #     if side:
    #         filter_kwargs['device_info__orientation'] = side
    #     return Asset.objects.select_related(
    #         'model', 'device_info', 'model__category'
    #     ).filter(**filter_kwargs).exclude(model__category__is_blade=True)

    # def __unicode__(self):
    #     name = self.name
    #     if self.server_room:
    #         name = '{} - {}'.format(name, self.server_room)
    #     elif self.data_center:
    #         name = '{} - {}'.format(name, self.data_center)
    #     return name


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

    def __unicode__(self):
        return '%s %s' % (self.manufacturer, self.name)

    def _get_layout_class(self, field):
        item = ModelVisualizationLayout.from_id(field)
        return getattr(item, 'css_class', '')

    def get_front_layout_class(self):
        return self._get_layout_class(self.visualization_layout_front)

    def get_back_layout_class(self):
        return self._get_layout_class(self.visualization_layout_back)


class Category(NamedMixin.NonUnique, TimeStampMixin, models.Model):
    code = models.CharField(max_length=4, blank=True, default='')
    is_blade = models.BooleanField()

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    def __unicode__(self):
        return self.name


class Warehouse(NamedMixin, TimeStampMixin, models.Model):
    pass


class AssetLastHostname(models.Model):
    prefix = models.CharField(max_length=8, db_index=True)
    counter = models.PositiveIntegerField(default=1)
    postfix = models.CharField(max_length=8, db_index=True)

    class Meta:
        unique_together = ('prefix', 'postfix')

    def __unicode__(self):
        return self.formatted_hostname()

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


# TODO: discuss
class ConnectionType(Choices):
    _ = Choices.Choice

    network = _("network connection")


class Connection(models.Model):

    outbound = models.ForeignKey(
        'DCAsset',
        verbose_name=_("connected to device"),
        on_delete=models.PROTECT,
        related_name='outbound_connections',
    )
    inbound = models.ForeignKey(
        'DCAsset',
        verbose_name=_("connected device"),
        on_delete=models.PROTECT,
        related_name='inbound_connections',
    )
    # TODO: discuss
    connection_type = models.PositiveIntegerField(
        verbose_name=_("connection type"),
        choices=ConnectionType()
    )

    def __unicode__(self):
        return "%s -> %s (%s)" % (
            self.outbound,
            self.inbound,
            self.connection_type
        )


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


class DCAsset(BasePhysicalAsset, Asset):
    rack = models.ForeignKey(Rack)

    # TODO: maybe move to objectModel?
    slots = models.FloatField(
        verbose_name='Slots',
        help_text=('For blade centers: the number of slots available in this '
                   'device. For blade devices: the number of slots occupied.'),
        max_length=64,
        default=0,
    )
    slot_no = models.CharField(
        verbose_name=_('slot number'), max_length=3, null=True, blank=True,
        help_text=_('Fill it if asset is blade server'),
    )
    # TODO: convert to foreign key
    configuration_path = models.CharField(
        _('configuration path'),
        max_length=100,
        help_text=_('Path to configuration for e.g. puppet, chef.'),
    )
    position = models.IntegerField(null=True)
    orientation = models.PositiveIntegerField(
        choices=Orientation(),
        default=Orientation.front.id,
    )

    class Meta:
        verbose_name = _('DC Asset')
        verbose_name_plural = _('DC Assets')

    @property
    def cores_count(self):
        """Returns cores count assigned to device in Ralph"""
        asset_cores_count = self.model.cores_count if self.model else 0
        return asset_cores_count

    connections = models.ManyToManyField(
        'self',
        through='Connection',
        symmetrical=False,
    )


class Database(Asset):
    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')


class VIP(Asset):
    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')


class VirtualServer(Asset):
    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')


class CloudProject(Asset):
    pass


class BOAsset(Asset, BasePhysicalAsset):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_owner',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_user',
    )
    location = models.CharField(max_length=128, null=True, blank=True)

    class Meta:
        verbose_name = _('BO Asset')
        verbose_name_plural = _('BO Assets')

    @property
    def country_code(self):
        return 'PL'
        # utils
        # iso2 = Country.name_from_id(self.owner.profile.country).upper()
        # return iso2_to_iso3.get(iso2, 'POL')


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

    def __unicode__(self):
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


class DiskShare(Component):
    share_id = models.PositiveIntegerField(
        verbose_name=_('share identifier'), null=True, blank=True,
    )
    label = models.CharField(
        verbose_name=_('name'), max_length=255, blank=True, null=True,
        default=None,
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'), null=True, blank=True,
    )
    snapshot_size = models.PositiveIntegerField(
        verbose_name=_('size for snapshots (MiB)'), null=True, blank=True,
    )
    wwn = models.CharField(
        verbose_name=_('Volume serial'), max_length=33, unique=True,
    )
    full = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('disk share')
        verbose_name_plural = _('disk shares')

    def __unicode__(self):
        return '%s (%s)' % (self.label, self.wwn)

    def get_total_size(self):
        return (self.size or 0) + (self.snapshot_size or 0)


class DiskShareMount(models.Model):
    share = models.ForeignKey(DiskShare, verbose_name=_("share"))
    asset = models.ForeignKey(
        'Asset', verbose_name=_('asset'), null=True, blank=True,
        default=None, on_delete=models.SET_NULL
    )
    volume = models.CharField(
        verbose_name=_('volume'), max_length=255, blank=True,
        null=True, default=None
    )
    size = models.PositiveIntegerField(
        verbose_name=_('size (MiB)'), null=True, blank=True,
    )

    class Meta:
        unique_together = ('share', 'asset')
        verbose_name = _('disk share mount')
        verbose_name_plural = _('disk share mounts')

    def __unicode__(self):
        return '%s@%r' % (self.volume, self.asset)

    def get_total_mounts(self):
        return self.share.disksharemount_set.exclude(
            device=None
        ).filter(
            is_virtual=False
        ).count()

    def get_size(self):
        return self.size or self.share.get_total_size()

# # # todo regionalized
# # class Asset(TimeStampMixin, PolymorphicModel):
# #     '''
# #     Asset model contain fields with basic information about single asset
# #     '''




# #     def get_data_type(self):
# #         # FIXME - merge part management
# #         return 'device'

# #     def _try_assign_hostname(self, commit):
# #         if self.owner and self.model.category and self.model.category.code:
# #             template_vars = {
# #                 'code': self.model.category.code,
# #                 'country_code': self.country_code,
# #             }
# #             if not self.hostname:
# #                 self.generate_hostname(commit, template_vars)
# #             else:
# #                 user_country = get_user_iso3_country_name(self.owner)
# #                 different_country = user_country not in self.hostname
# #                 if different_country:
# #                     self.generate_hostname(commit, template_vars)

# #     @property
# #     def exists(self):
# #         """Check if object is a new db record"""
# #         return self.pk is not None

# #     def save(self, commit=True, force_unlink=False, *args, **kwargs):
# #         _replace_empty_with_none(self, ['source', 'hostname'])
# #         return super(Asset, self).save(commit=commit, *args, **kwargs)

# #     def get_data_icon(self):
# #         return 'fugue-computer'



# #     # @nested_commit_on_success


# #     def get_related_assets(self):
# #         """Returns the children of a blade chassis"""
# #         return 'TODO'
# #         # orientations = [Orientation.front, Orientation.back]
# #         # assets_by_orientation = []
# #         # for orientation in orientations:
# #         #     assets_by_orientation.append(list(
# #         #         Asset.objects.select_related('device_info', 'model').filter(
# #         #             device_info__position=self.device_info.position,
# #         #             device_info__rack=self.device_info.rack,
# #         #             device_info__orientation=orientation,
# #         #         ).exclude(id=self.id)
# #         #     ))
# #         # assets = [
# #         #     Gap.generate_gaps(assets) for assets in assets_by_orientation
# #         # ]
# #         # return chain(*assets)

# #     def get_orientation_desc(self):
# #         return self.device_info.get_orientation_desc()

# #     def get_configuration_url(self):
# #         # FIXME: what is purpose of this?
# #         # device = self.get_ralph_device()
# #         # configuration_url = self.url if device else None
# #         # return configuration_url
# #         return ''  # self.url

# #     def get_vizualization_url(self):
# #         try:
# #             rack_id, data_center_id = (
# #                 self.device_info.rack.id, self.device_info.rack.data_center.id,
# #             )
# #         except AttributeError:
# #             visualization_url = None
# #         else:
# #             prefix = reverse('dc_view')
# #             postfix = '/dc/{data_center_id}/rack/{rack_id}'.format(
# #                 data_center_id=data_center_id, rack_id=rack_id,
# #             )
# #             visualization_url = '#'.join([prefix, postfix])
# #         return visualization_url


# # class DCAsset(Asset):



# #     # Ralph 3.0 --  new fields

# #     # server blade -> chassis blade
# #     # virtual -> hypervisor
# #     # 2 switches -> stacked switch
# #     # database -> db server - to be discussed
# #     parent = models.ForeignKey(
# #         'self',
# #         verbose_name=_("physical parent device"),
# #         on_delete=models.SET_NULL,
# #         null=True,
# #         blank=True,
# #         default=None,
# #         related_name="child_set",
# #     )


# #     # Configuration path

# #     # configuration_path = models.CharField(max_length=10, null=True, blank=True)

# #     # TODO
# #     # puppet_venture = models.ForeignKey(
# #     #     PuppetVenture,
# #     #     verbose_name=_("puppet venture"),
# #     #     null=True,
# #     #     blank=True,
# #     #     default=None,
# #     #     on_delete=db.SET_NULL,
# #     # )

# #     # puppet_venture_role = models.ForeignKey(
# #     #     PuppetVentureRole,
# #     #     on_delete=db.SET_NULL,
# #     #     verbose_name=_("puppet venture role"),
# #     #     null=True,
# #     #     blank=True,
# #     #     default=None,
# #     # )

# #     # management = models.ForeignKey(
# #     #     'IPAddress',
# #     #     related_name="managed_set",
# #     #     verbose_name=_("management address"),
# #     #     null=True,
# #     #     blank=True,
# #     #     default=None,
# #     #     on_delete=db.SET_NULL,
# #     # )

# #     # verified = models.BooleanField(verbose_name=_("verified"), default=False)
# #     def get_absolute_url(self):
# #         return reverse('device_edit', kwargs={
# #             'mode': 'dc',
# #             'asset_id': self.id,
# #         })
