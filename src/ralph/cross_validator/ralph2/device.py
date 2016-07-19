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
    sn = models.CharField(max_length=255)
    parent = models.ForeignKey('self', related_name='child_set', null=True)
    logical_parent = models.ForeignKey(
        'self', related_name='logicalchild_set', null=True
    )
    purchase_date = models.DateTimeField()

    service = models.ForeignKey(ServiceCatalog, default=None)
    device_environment = models.ForeignKey(DeviceEnvironment)
    venture = models.ForeignKey('Venture', null=True)
    venture_role = models.ForeignKey('VentureRole', null=True)

    _excludes = ['deleted', 'logicalchild_set', 'deviceinfo']

    class Meta(generate_meta(app_label='discovery', model_name='device')):
        pass

    @property
    def asset(self):
        return Asset.objects.filter(
            device_info__ralph_device_id=self.pk
        ).first()

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
    ralph_device = models.OneToOneField(Device, null=True)
    u_level = models.CharField(max_length=10, null=True, blank=True)
    u_height = models.CharField(max_length=10, null=True, blank=True)
    rack = models.ForeignKey(Rack, null=True, blank=True)
    slot_no = models.CharField(max_length=3)
    position = models.IntegerField(null=True)

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
    service = models.ForeignKey(ServiceCatalog, default=None)
    device_environment = models.ForeignKey(DeviceEnvironment)

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


class Venture(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, related_name="child_set")
    symbol = models.CharField(max_length=32)

    class Meta(generate_meta(app_label='business', model_name='venture')):
        pass


class VentureRole(models.Model):
    name = models.CharField(max_length=255)
    venture = models.ForeignKey(Venture)

    class Meta(generate_meta(app_label='business', model_name='venturerole')):
        pass

    def get_properties(self, device):
        def property_dict(properties):
            props = {}
            for prop in properties:
                try:
                    pv = prop.rolepropertyvalue_set.get(device=device)
                except RolePropertyValue.DoesNotExist:
                    value = prop.default
                else:
                    value = pv.value
                props[prop.symbol] = value or ''
            return props
        values = {}
        values.update(property_dict(
            self.venture.roleproperty_set.filter(role=None),
        ))
        values.update(property_dict(
            self.roleproperty_set.filter(venture=None),
        ))
        return values


class RolePropertyType(models.Model):
    symbol = models.CharField(max_length=32, null=True)

    class Meta(generate_meta(
        app_label='business', model_name='rolepropertytype'
    )):
        pass


class RolePropertyTypeValue(models.Model):
    type = models.ForeignKey(RolePropertyType, null=True,)
    value = models.TextField(null=True)

    class Meta(generate_meta(
        app_label='business', model_name='rolepropertytypevalue'
    )):
        pass


class RoleProperty(models.Model):
    symbol = models.CharField(max_length=32, null=True)
    role = models.ForeignKey(VentureRole, null=True)
    venture = models.ForeignKey(Venture, null=True)
    type = models.ForeignKey(RolePropertyType, null=True)
    default = models.TextField(null=True)

    class Meta(generate_meta(
        app_label='business', model_name='roleproperty'
    )):
        pass


class RolePropertyValue(models.Model):
    property = models.ForeignKey(RoleProperty, null=True)
    device = models.ForeignKey(Device, null=True)
    value = models.TextField(null=True, default=None)

    class Meta(generate_meta(
        app_label='business', model_name='rolepropertyvalue'
    )):
        pass
