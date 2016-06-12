from django.db import models
from ralph.cross_validator.ralph2 import generate_meta, SoftDeletable
from ralph.cross_validator.ralph2 import cmdb as models_ci


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
    parent = models.ForeignKey('self', related_name='child_set')
    logical_parent = models.ForeignKey('self', related_name='logicalchild_set')
    purchase_date = models.DateTimeField()

    service = models.ForeignKey(ServiceCatalog, default=None)
    device_environment = models.ForeignKey(DeviceEnvironment)

    _excludes = ['deleted', 'logicalchild_set', 'deviceinfo']

    class Meta(generate_meta(app_label='discovery', model_name='device')):
        pass


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

    class Meta(generate_meta(app_label='ralph_assets', model_name='deviceinfo')):  # noqa
        pass

    def get_ralph_device(self):
        if not self.ralph_device:
            return None
        try:
            dev = Device.objects.get(id=self.ralph_device.id)
            return dev
        except Device.DoesNotExist:
            return None


class AssetModel(models.Model):
    name = models.CharField(max_length=255)

    class Meta(generate_meta(app_label='ralph_assets', model_name='assetmodel')):
        pass


class Asset(models.Model):
    device_info = models.OneToOneField(DeviceInfo)
    sn = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)
    niw = models.CharField(max_length=200)
    model = models.ForeignKey(AssetModel)

    _excludes = ['device_info_id']

    class Meta(generate_meta(app_label='ralph_assets', model_name='asset')):
        pass

    @property
    def linked_device(self):
        try:
            device = self.device_info.get_ralph_device()
        except Exception:
            device = None
        return device
