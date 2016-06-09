from dj.choices import Choices

from django.db import models

from ralph.cross_validator.ralph2 import cmdb as models_ci
from ralph.cross_validator.ralph2 import generate_meta, SoftDeletable


class ServiceCatalogManager(models.Manager):
    def get_query_set(self):
        return super().get_query_set().filter(
            type=models_ci.CI_TYPES.SERVICE,
            state=models_ci.CI_STATE_TYPES.ACTIVE,
        )


class ServiceCatalog(models_ci.CI):
    class Meta:
        proxy = True


class DeviceEnvironmentManager(models.Manager):
    def get_query_set(self):
        return super(DeviceEnvironmentManager, self).get_query_set().filter(
            type__name=models_ci.CI_TYPES.ENVIRONMENT,
            state=models_ci.CI_STATE_TYPES.ACTIVE,
        )


class DeviceEnvironment(models_ci.CI):
    objects = DeviceEnvironmentManager()

    class Meta:
        proxy = True


class Device(SoftDeletable, models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', related_name='child_set', null=True)
    logical_parent = models.ForeignKey(
        'self', related_name='logicalchild_set', null=True
    )
    purchase_date = models.DateTimeField()

    service = models.ForeignKey(ServiceCatalog, default=None)
    device_environment = models.ForeignKey(DeviceEnvironment)

    _excludes = ['deleted', 'logicalchild_set', 'deviceinfo']

    class Meta(generate_meta(app_label='discovery', model_name='device')):
        pass

    @property
    def management_ip(self):
        for ip in self.ipaddress_set.all():
            if ip.is_management:
                return ip.address


class Rack(models.Model):
    name = models.CharField(max_length=255)

    class Meta(generate_meta(app_label='ralph_assets', model_name='rack')):
        pass


class DeviceInfo(SoftDeletable, models.Model):
    ralph_device = models.OneToOneField(Device)
    u_level = models.CharField(max_length=10, null=True, blank=True)
    u_height = models.CharField(max_length=10, null=True, blank=True)
    # data_center = models.ForeignKey(DataCenter, null=True, blank=False)
    # server_room = models.ForeignKey(ServerRoom, null=True, blank=False)
    rack = models.ForeignKey(Rack, null=True, blank=True)
    # # deperecated field, use rack instead
    # rack_old = models.CharField(max_length=10, null=True, blank=True)
    slot_no = models.CharField(max_length=3)
    position = models.IntegerField(null=True)
    # orientation = models.PositiveIntegerField(
    #     choices=Orientation(),
    #     default=Orientation.front.id,
    # )

    class Meta(
        generate_meta(app_label='ralph_assets', model_name='deviceinfo')
    ):
        pass

    def get_ralph_device(self):
        return self.ralph_device


class AssetModel(models.Model):
    name = models.CharField(max_length=255)

    class Meta(
        generate_meta(app_label='ralph_assets', model_name='assetmodel')
    ):
        pass


class AssetType(Choices):
    _ = Choices.Choice

    DC = Choices.Group(0)
    data_center = _("data center")

    BO = Choices.Group(100)
    back_office = _("back office")
    administration = _("administration")

    OTHER = Choices.Group(200)
    other = _("other")


class DCAdminManager(models.Manager):
    def get_query_set(self):
        return super(DCAdminManager, self).get_query_set().filter(
            type__in=(AssetType.DC.choices)
        )


class Asset(models.Model):
    device_info = models.OneToOneField(DeviceInfo)
    sn = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)
    niw = models.CharField(max_length=200)
    model = models.ForeignKey(AssetModel)

    _excludes = ['device_info_id']

    objects = DCAdminManager()

    class Meta(generate_meta(app_label='ralph_assets', model_name='asset')):
        pass

    @property
    def linked_device(self):
        try:
            device = self.device_info.get_ralph_device()
        except Exception:
            device = None
        return device


class IPAddress(models.Model):
    address = models.IPAddressField()
    is_management = models.BooleanField(default=False)
    device = models.ForeignKey('Device', null=True)

    class Meta(generate_meta(app_label='discovery', model_name='ipaddress')):
        pass
