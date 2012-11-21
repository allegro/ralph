#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.related import ForeignKey
from lck.django.common.models import TimeTrackable
from lck.django.choices import Choices

from ralph.discovery.models_device import Device as RalphDevice


class LicenseTypes(Choices):
    _ = Choices.Choice
    oem = _("oem")
    box = _("box")


class Status(Choices):
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


class Asset(TimeTrackable):
    source = models.IntegerField(choices=AssetSource())
    invoice_no = models.CharField(max_length=30)
    buy_date = models.DateField(default=datetime.datetime.now)
    sn = models.CharField(max_length=200)
    barcode = models.CharField(max_length=200)
    support_period = models.IntegerField(
        verbose_name="Support period in months")
    support_type = models.CharField(max_length=512)  # FIXME: wyjasnic czy lista/hybryda czy text
    support_void_reporting = models.BooleanField()
    model = ForeignKey('Model')
    backoffice_data = ForeignKey('BackOfficeData', null=True, blank=True)


class AssetStatus(TimeTrackable):
    device = ForeignKey('Device')
    status = models.IntegerField(
        choices=Status(),
        verbose_name=_("relation kind")
    )


class Device(TimeTrackable):
    ralph_device = ForeignKey(RalphDevice, null=True)
    size = models.IntegerField(
        verbose_name='Size in units',
        default=0
    )
    location = models.CharField(
        max_length=255,
        verbose_name="A place where device is currently located in."
        " May be DC/Rack or City/branch"
    )


class Part(Asset,TimeTrackable):
    barcode_recovery = models.CharField(max_length=50)
    source_device = ForeignKey(
        'Device',
        related_name = 'source_device',
        null=True, blank=True,
    )
    device = ForeignKey('Device', related_name='device',null=True, blank=True)


class Model(TimeTrackable):
    name =  models.CharField(max_length=100)
    vendor = models.CharField(max_length=100)


def content_file_name(instance, filename):
    return '/'.join(['content', instance.user.username, filename])


class BackOfficeData(TimeTrackable):
    cost_centre = models.CharField(max_length=100)
    license_key = models.CharField(max_length=255)
    version = models.IntegerField()
    provider = models.CharField(max_length=255)  # dostawca != producent
    order_no = models.CharField(max_length=50)  # nr zamowienia
    unit_price = models.DecimalField(
        max_digits=20,decimal_places=2,default=0
    )  # koszt jednostkowy
    attachment = models.FileField(upload_to=content_file_name)
    license_type = models.IntegerField(choices=LicenseTypes())
    date_of_last_inventory = models.DateField()
    last_logged_user = models.CharField(max_length=100)


