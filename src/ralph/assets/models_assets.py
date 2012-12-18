#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Asset management models."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import os

from django.db import models
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import (
    TimeTrackable, EditorTrackable, SoftDeletable, Named
)
from lck.django.choices import Choices
from uuid import uuid4
from ralph.business.models import Venture
from ralph.discovery.models_device import Device, DeviceType
from ralph.discovery.models_util import SavingUser


SAVE_PRIORITY = 0


class LicenseType(Choices):
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


class AssetManufacturer(TimeTrackable, EditorTrackable, Named.NonUnique):
    def __unicode__(self):
        return self.name


class AssetModel(TimeTrackable, EditorTrackable, Named.NonUnique):
    manufacturer = models.ForeignKey(
        AssetManufacturer, on_delete=models.PROTECT)

    def __unicode__(self):
        return "%s %s" % (self.manufacturer.name, self.name)


class Warehouse(TimeTrackable, EditorTrackable, Named.NonUnique):
    def __unicode__(self):
        return self.name


def _get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid4(), ext)
    return os.path.join('assets', filename)


class Asset(TimeTrackable, EditorTrackable, SavingUser, SoftDeletable):
    device_info = models.OneToOneField(
        'DeviceInfo', null=True, blank=True, on_delete=models.CASCADE
    )
    part_info = models.OneToOneField(
        'PartInfo', null=True, blank=True, on_delete=models.CASCADE
    )
    office_info = models.OneToOneField(
        'OfficeInfo', null=True, blank=True, on_delete=models.CASCADE
    )
    type = models.PositiveSmallIntegerField(choices=AssetType())
    model = models.ForeignKey(AssetModel, on_delete=models.PROTECT)
    source = models.PositiveIntegerField(
        verbose_name=_("source"), choices=AssetSource(), db_index=True
    )
    invoice_no = models.CharField(
        max_length=30, db_index=True, null=True, blank=True
    )
    order_no = models.CharField(max_length=50, null=True, blank=True)
    invoice_date = models.DateField(default=datetime.date.today)
    sn = models.CharField(max_length=200, unique=True)
    barcode = models.CharField(
        max_length=200, null=True, blank=True, unique=True
    )
    support_period = models.PositiveSmallIntegerField(
        verbose_name="support period in months")
    support_type = models.CharField(max_length=150)
    support_void_reporting = models.BooleanField(default=True, db_index=True)
    provider = models.CharField(max_length=100, null=True, blank=True)
    status = models.PositiveSmallIntegerField(
        default=AssetStatus.new.id,
        verbose_name=_("status"),
        choices=AssetStatus()
    )
    remarks = models.CharField(
        verbose_name='Additional remarks',
        max_length=1024, blank=True
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)

    def __unicode__(self):
        return "{} - {} - {}".format(self.model, self.sn, self.barcode)

    @classmethod
    def objects_bo(cls):
        """Returns back office assets queryset"""
        return cls.objects.filter(
            type__in=(AssetType.administration, AssetType.back_office)
        )

    @classmethod
    def objects_dc(cls):
        """Returns data center assets queryset"""
        return cls.objects.filter(type=AssetType.data_center)

    def get_data_type(self):
        if self.device_info:
            return 'device'
        elif self.part_info:
            return 'part'
        else:
            # should not return this value ;-)
            return 'Unknown'

    def get_data_icon(self):
        if self.get_data_type() == 'device':
            return 'fugue-computer'
        elif self.get_data_type() == 'part':
            return 'fugue-box'
        else:
            raise UserWarning('Unknown asset data type!')

    def create_stock_device(self):
        try:
            device = Device.objects.get(sn=self.sn)
        except Device.DoesNotExist:
            try:
                venture = Venture.objects.get(name='Stock')
            except Venture.DoesNotExist:
                venture = Venture(name='Stock', symbol='stock')
                venture.save()
            device = Device.create(
                sn=self.sn,
                model_name='Unknown',
                model_type=DeviceType.unknown,
                priority=SAVE_PRIORITY,
                venture=venture,
                name='Unknown',
            )
        self.device_info.ralph_device = device
        self.device_info.save()

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.saving_user = None
        super(Asset, self).__init__(*args, **kwargs)


class DeviceInfo(TimeTrackable, SavingUser):
    ralph_device = models.ForeignKey(
        'discovery.Device', null=True, blank=True, on_delete=models.SET_NULL
    )
    size = models.PositiveSmallIntegerField(
        verbose_name='Size in units', default=1)

    def __unicode__(self):
        return "{} - {} - {}".format(
            self.ralph_device,
            self.size,
        )

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.saving_user = None
        super(DeviceInfo, self).__init__(*args, **kwargs)


class OfficeInfo(TimeTrackable, SavingUser):
    license_key = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(
        max_digits=20, decimal_places=2, default=0)
    attachment = models.FileField(
        upload_to=_get_file_path, blank=True)
    license_type = models.IntegerField(
        choices=LicenseType(), verbose_name=_("license type"),
        null=True, blank=True
    )
    date_of_last_inventory = models.DateField(
        null=True, blank=True)
    last_logged_user = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return "{} - {} - {}".format(
            self.license_key,
            self.version,
            self.license_type
        )

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.saving_user = None
        super(OfficeInfo, self).__init__(*args, **kwargs)


class PartInfo(TimeTrackable, SavingUser):
    barcode_salvaged = models.CharField(max_length=200, null=True, blank=True)
    source_device = models.ForeignKey(
        Asset, null=True, blank=True, related_name='source_device'
    )
    device = models.ForeignKey(
        Asset, null=True, blank=True, related_name='device'
    )

    def __unicode__(self):
        return "{} - {}".format(self.device, self.barcode_salvaged)

    def __init__(self, *args, **kwargs):
        self.save_comment = None
        self.saving_user = None
        super(PartInfo, self).__init__(*args, **kwargs)
