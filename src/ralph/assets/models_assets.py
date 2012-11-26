#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Asset management models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from lck.django.common.models import TimeTrackable, EditorTrackable
from lck.django.choices import Choices


class LicenseTypes(Choices):
    _ = Choices.Choice
    not_applicable = _("not applicable")
    oem = _("oem")
    box = _("box")


class AssetType(Choices):
    _ = Choices.Choice

    DC = Choices.Group(0)
    data_center = _("data center")

    BO = Choices.Group(100)
    back_office = _("back office")
    administration = _("administration")


class AssetStatus(Choices):
    _ = Choices.Choice

    HARDWARE = Choices.Group(0)
    new = _("new")
    in_progress = _("in progress")
    waiting_for_release = _("waiting for release")
    used = _("used")
    loan = _("loan")
    damaged = _("damaged")
    liquidated = _("liquidated")
    in_service = _("in service")
    in_repair = _("in repair")
    ok = _("ok")

    SOFTWARE = Choices.Group(100)
    installed = _("installed")
    free = _("free")
    reserved = _("reserved")


class AssetSource(Choices):
    _ = Choices.Choice

    shipment = _("shipment")
    salvaged = _("salvaged")


class AssetManufacturer(TimeTrackable, EditorTrackable):
    name = models.CharField(max_length=250)

    def __unicode__(self):
        return "{}".format(self.name)


class AssetModel(TimeTrackable, EditorTrackable):
    manufacturer = models.ForeignKey(AssetManufacturer,
                                     on_delete=models.PROTECT)
    name = models.CharField(max_length=250)

    def __unicode__(self):
        return "{}".format(self.name)


class Warehouse(TimeTrackable, EditorTrackable):
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


def content_file_name(instance, filename):
    return '/'.join(['assets', str(instance.pk), filename])


class OfficeInfo(models.Model):
    license_key = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=50, null=True, blank=True)
    unit_price = models.DecimalField(
        max_digits=20, decimal_places=2, default=0)
    attachment = models.FileField(upload_to=content_file_name, null=True,
                                  blank=True)
    license_type = models.IntegerField(choices=LicenseTypes(),
                                       verbose_name=_("license type"),
                                       null=True, blank=True)
    date_of_last_inventory = models.DateField(null=True, blank=True)
    last_logged_user = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return "{} - {} - {}".format(
            self.license_key,
            self.version,
            self.license_type
        )


class Asset(TimeTrackable, EditorTrackable):
    device_info = models.OneToOneField('DeviceInfo', null=True, blank=True)
    part_info = models.OneToOneField('PartInfo', null=True, blank=True)
    office_info = models.OneToOneField(
        OfficeInfo, null=True, blank=True,
        on_delete=models.SET_NULL)
    type = models.PositiveSmallIntegerField(choices=AssetType())
    model = models.ForeignKey(AssetModel, on_delete=models.PROTECT)
    source = models.PositiveIntegerField(verbose_name=_("source"),
                                         choices=AssetSource(),
                                         db_index=True)
    invoice_no = models.CharField(
        max_length=30, db_index=True, null=True, blank=True)
    order_no = models.CharField(max_length=50, null=True, blank=True)
    buy_date = models.DateField(default=datetime.date.today())
    sn = models.CharField(max_length=200, unique=True)
    barcode = models.CharField(max_length=200, null=True, blank=True,
                               unique=True)
    support_period = models.PositiveSmallIntegerField(
        verbose_name="support period in months")
    support_type = models.CharField(max_length=150)
    support_void_reporting = models.BooleanField(default=False, db_index=True)
    provider = models.CharField(max_length=100, null=True, blank=True)
    status = models.PositiveSmallIntegerField(verbose_name=_("status"),
                                              choices=AssetStatus())
    remarks = models.CharField(max_length=1024)

    def __unicode__(self):
        return "{} - {} - {}".format(self.model, self.sn, self.barcode)

    @classmethod
    def objects_bo(self):
        """Returns back office assets queryset"""
        return Asset.objects.filter(type=AssetType.back_office)

    @classmethod
    def objects_dc(self):
        """Returns data center assets queryset"""
        return Asset.objects.filter(type=AssetType.data_center)


class DeviceInfo(TimeTrackable):
    ralph_device = models.ForeignKey('discovery.Device', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    size = models.PositiveSmallIntegerField(verbose_name='Size in units',
                                            default=1)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)

    def __unicode__(self):
        return "{}".format(self.ralph_device)


class PartInfo(TimeTrackable):
    barcode_salvaged = models.CharField(max_length=200, null=True, blank=True)
    source_device = models.ForeignKey(
        Asset, null=True, blank=True, related_name='source_device')
    device = models.ForeignKey(
        Asset, null=True, blank=True, related_name='device')

    def __unicode__(self):
        return "{}".format(self.barcode_salvaged)


