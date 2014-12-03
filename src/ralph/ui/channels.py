# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied

from ajax_select import LookupChannel
from django.db import models as db
from django.utils.html import escape

from ralph.business.models import Venture
from ralph.discovery import models_device
from ralph.discovery.models import Device
from ralph.util import presentation


class RestrictedLookupChannel(LookupChannel):
    """
    Base lookup returning results only if request user is authenticated.
    """
    def check_auth(self, request):
        """
        Write restriction rules here.
        """
        if not request.user.is_authenticated():
            raise PermissionDenied

    def get_query(self, text, request):
        founds = self.model.objects.filter(
            name__icontains=text
        ).order_by('name')[:10]
        return founds

    def get_result(self, obj):
        return obj.name

    def get_item_url(self, obj):
        return getattr(obj, 'url', None)

    def format_match(self, obj):
        return self.format_item_display(obj)

    def format_item_display(self, obj):
        return '{}'.format(escape(unicode(obj.name)))

    def get_base_objects(self):
        return self.model.objects


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


class ServiceCatalogLookup(RestrictedLookupChannel):
    model = models_device.ServiceCatalog


class DeviceEnvironmentLookup(RestrictedLookupChannel):
    model = models_device.DeviceEnvironment

    def get_query(self, query, request):
        try:
            service = models_device.ServiceCatalog.objects.get(id=query)
        except models_device.ServiceCatalog.DoesNotExist:
            envs = models_device.ServiceCatalog.objects.none()
        else:
            envs = service.get_environments()
        return envs


class VentureLookup(RestrictedLookupChannel):
    model = Venture
