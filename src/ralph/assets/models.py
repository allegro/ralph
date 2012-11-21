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

from ralph.discovery.models_device import Device as RalphDevice


class LicenseTypes(Choices):
    oem = _("oem")
    box = _("box")


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
    recovery = _("recovery")


class AssetManufacturer(TimeTrackable, EditorTrackable):
    name = models.CharField(max_length=250)


class AssetModel(TimeTrackable, EditorTrackable):
    manufacturer = models.ForeignKey(AssetManufacturer,
                                     on_delete=models.PROTECT)
    name = models.CharField(max_length=250)


def content_file_name(instance, filename):
    return '/'.join(['content', instance.user.username, filename])


class BackOfficeData(models.Model):
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


class Asset(TimeTrackable, EditorTrackable):
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
    back_office_data = models.ForeignKey(BackOfficeData, null=True, blank=True,
                                         on_delete=models.SET_NULL)
    status = models.PositiveSmallIntegerField(verbose_name=_("status"),
                                              choices=AssetStatus())

    class Meta:
        abstract = True


class Device(Asset):
    ralph_device = models.ForeignKey(RalphDevice, null=True, blank=True,
                                     on_delete=models.SET_NULL)
    size = models.PositiveSmallIntegerField(verbose_name='Size in units',
                                            default=1)
    location = models.CharField(
        max_length=250,
        verbose_name="A place where device is currently located in."
        " May be DC/Rack or City/branch"
    )


class Part(Asset):
    barcode_recovery = models.CharField(max_length=200, null=True, blank=True)
    source_device = models.ForeignKey(Device, null=True, blank=True)
    device = models.ForeignKey(Device, null=True, blank=True)

