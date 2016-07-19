from django.db import models

from ralph.cross_validator.ralph2 import generate_meta
from ralph.cross_validator.ralph2.device import Device


class DataCenter(models.Model):
    name = models.CharField(max_length=255)

    class Meta(generate_meta(app_label='discovery', model_name='datacenter')):
        pass


class NetworkKind(models.Model):
    name = models.CharField(max_length=255)

    class Meta(generate_meta(app_label='discovery', model_name='networkkind')):
        pass


class Environment(models.Model):
    name = models.CharField(max_length=255)
    data_center = models.ForeignKey(DataCenter)

    class Meta(generate_meta(app_label='discovery', model_name='environment')):
        pass


class NetworkTerminator(models.Model):
    name = models.CharField(max_length=255)

    class Meta(generate_meta(app_label='discovery', model_name='networkterminator')):  # noqa
        pass


class DNSServer(models.Model):
    ip_address = models.IPAddressField(unique=True)
    is_default = models.BooleanField(default=False)

    class Meta(generate_meta(app_label='dnsedit', model_name='DNSServer')):
        pass


class Network(models.Model):
    address = models.CharField(max_length='30', unique=True)
    gateway = models.IPAddressField(blank=True, null=True, default=None)
    reserved = models.PositiveIntegerField(default=10)
    reserved_top_margin = models.PositiveIntegerField(default=0)
    remarks = models.TextField(blank=True, default="")
    terminators = models.ManyToManyField("NetworkTerminator")
    vlan = models.PositiveIntegerField(null=True, blank=True, default=None)
    data_center = models.ForeignKey(DataCenter, null=True, blank=True)
    environment = models.ForeignKey(Environment, null=True, blank=True)
    kind = models.ForeignKey(NetworkKind, null=True, blank=True, default=None)
    racks = models.ManyToManyField(Device)
    custom_dns_servers = models.ManyToManyField(DNSServer, null=True)
    dhcp_broadcast = models.BooleanField(default=False)

    class Meta(generate_meta(app_label='discovery', model_name='network')):
        pass
