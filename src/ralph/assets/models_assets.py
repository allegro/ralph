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
from ralph.discovery.models_util import SavingUser


class LicenseTypes(Choices):
    _ = Choices.Choice
    oem = _("oem")
    box = _("box")


class AssetType(Choices):
    _ = Choices.Choice
    back_office = _("back office")
    data_center = _("data center")
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


def content_file_name(instance, filename):
    return '/'.join(['content', instance.user.username, filename])


class OfficeData(models.Model):
    license_key = models.CharField(max_length=255, null=True, blank=True)
    version = models.CharField(max_length=50, null=True, blank=True)
    order_no = models.CharField(max_length=50, null=True, blank=True)
    unit_price = models.DecimalField(max_digits=20, decimal_places=2,
                                     default=0)
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


class Asset(TimeTrackable, EditorTrackable, SavingUser):
    device_info = models.OneToOneField('DeviceInfo', null=True, blank=True)
    part_info = models.OneToOneField('PartInfo', null=True, blank=True)
    office_data = models.OneToOneField(
        OfficeData, null=True, blank=True,
        on_delete=models.SET_NULL)
    type = models.PositiveSmallIntegerField(choices=AssetType())
    model = models.ForeignKey(AssetModel, on_delete=models.PROTECT)
    source = models.PositiveIntegerField(verbose_name=_("source"),
                                         choices=AssetSource(),
                                         db_index=True)
    invoice_no = models.CharField(max_length=30, db_index=True)
    buy_date = models.DateField(default=datetime.datetime.now())
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

    def __unicode__(self):
        return "{} - {} - {}".format(self.model, self.sn,self.barcode)

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.being_deleted = False
        self.saving_user = None
        super(Asset, self).__init__(*args, **kwargs)

class DeviceInfo(TimeTrackable):
    ralph_device = models.ForeignKey('discovery.Device', null=True, blank=True,
                                     on_delete=models.SET_NULL)
    size = models.PositiveSmallIntegerField(verbose_name='Size in units',
                                            default=1)
    location = models.CharField(
        max_length=250,
        verbose_name="A place where device is currently located in."
                     " May be DC/Rack or City/branch"
    )
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
