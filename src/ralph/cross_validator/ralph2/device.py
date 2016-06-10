from django.db import models


def generate_meta(app_label, model_name):
    class Meta:
        managed = False
        db_table = '_'.join([app_label, model_name]).lower()
    return Meta


class SoftDeletableManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(deleted=False)
        return qs


class SoftDeletable(models.Model):
    deleted = models.BooleanField()
    objects = SoftDeletableManager()

    class Meta:
        abstract = True


class Device(SoftDeletable, models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', related_name='child_set')
    logical_parent = models.ForeignKey('self', related_name='logicalchild_set')
    purchase_date = models.DateTimeField()

    _excludes = ['deleted', 'logicalchild_set', 'deviceinfo']

    class Meta(generate_meta(app_label='discovery', model_name='device')):
        pass


class DeviceInfo(SoftDeletable, models.Model):
    ralph_device = models.OneToOneField(Device)
    u_level = models.CharField(max_length=10, null=True, blank=True)
    u_height = models.CharField(max_length=10, null=True, blank=True)
    # data_center = models.ForeignKey(DataCenter, null=True, blank=False)
    # server_room = models.ForeignKey(ServerRoom, null=True, blank=False)
    # rack = models.ForeignKey(Rack, null=True, blank=True)
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


class Asset(models.Model):
    device_info = models.OneToOneField(DeviceInfo)
    sn = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255)
    niw = models.CharField(max_length=200)

    _excludes = ['device_info_id']

    class Meta(generate_meta(app_label='ralph_assets', model_name='asset')):
        pass

    @property
    def linked_device(self):
        try:
            device = self.device_info.get_ralph_device()
        except AttributeError:
            device = None
        return device
