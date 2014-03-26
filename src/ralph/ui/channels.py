# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ajax_select import LookupChannel
from django.db import models as db
from django.utils.html import escape

from ralph.discovery.models import Device
from ralph.util import presentation


class DeviceLookup(LookupChannel):
    model = Device

    def get_query(self, q, request):
        return Device.objects.filter(
            db.Q(name__istartswith=q) |
            db.Q(sn__istartswith=q) |
            db.Q(barcode__istartswith=q)
        ).order_by('name')[:10]

    def get_result(self, obj):
        return obj.name

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return '<i class="fugue-icon %s"></i>&nbsp;%s <div><small>%s</small></div>' % (
            presentation.get_device_icon(obj),
            escape(obj.name),
            escape(obj.venture) + '/' + escape(obj.venture_role),
        )
