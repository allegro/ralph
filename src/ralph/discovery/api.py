#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""ReST API for Ralph's discovery models
   -------------------------------------

Done with TastyPie.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.discovery.models import Device, DeviceModel, DeviceModelGroup,\
    DeviceType, IPAddress

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFREME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']
SAVE_PRIORITY=10

class IPAddressResource(MResource):
    device = fields.ForeignKey('ralph.discovery.api.DevResource', 'device',
        null=True)

    class Meta:
        queryset = IPAddress.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'address': ALL,
            'hostname': ALL,
            'snmp_community': ALL,
            'device': ALL,
            'is_management': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority', 'dns_info',
            'snmp_name')
        cache = SimpleCache()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class ModelGroupResource(MResource):
    class Meta:
        queryset = DeviceModelGroup.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        cache = SimpleCache()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class ModelResource(MResource):
    group = fields.ForeignKey(ModelGroupResource, 'group', null=True,
        full=True)

    class Meta:
        queryset = DeviceModel.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        excludes = ('save_priorities', 'max_save_priority',)
        cache = SimpleCache()
        filtering = {
            'type': ALL,
        }
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class DeviceResource(MResource):
    model = fields.ForeignKey(ModelResource, 'model', null=True, full=True)
    management = fields.ForeignKey(IPAddressResource, 'management', null=True,
        full=True)
    venture = fields.ForeignKey('ralph.business.api.VentureLightResource',
        'venture', null=True, full=True)
    role = fields.ForeignKey('ralph.business.api.RoleResource',
        'venture_role', null=True, full=True)
    ip_addresses = fields.ToManyField(IPAddressResource, 'ipaddress',
        related_name='device', full=True)

    class Meta:
        excludes = ('raw', 'save_priorities', 'max_save_priority')
        filtering = {
            'model': ALL_WITH_RELATIONS,
            'sn': ALL,
            'barcode': ALL,
            'venture': ALL_WITH_RELATIONS,
            'role': ALL_WITH_RELATIONS,
            'ip_addresses': ALL_WITH_RELATIONS,
            'verified': ALL,
        }
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        cache = SimpleCache()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)

    def obj_update(self, bundle, request=None, **kwargs):
        """
        TAKEN FROM tastypie 0.9.11

        A ORM-specific implementation of ``obj_update``.
        """
        from tastypie.resources import NOT_AVAILABLE, ObjectDoesNotExist, NotFound
        if not bundle.obj or not bundle.obj.pk:
            # Attempt to hydrate data from kwargs before doing a lookup for the object.
            # This step is needed so certain values (like datetime) will pass model validation.
            try:
                bundle.obj = self.get_object_list(request).model()
                bundle.data.update(kwargs)
                bundle = self.full_hydrate(bundle)
                lookup_kwargs = kwargs.copy()

                for key in kwargs.keys():
                    if key == 'pk':
                        continue
                    elif getattr(bundle.obj, key, NOT_AVAILABLE) is not NOT_AVAILABLE:
                        lookup_kwargs[key] = getattr(bundle.obj, key)
                    else:
                        del lookup_kwargs[key]
            except:
                # if there is trouble hydrating the data, fall back to just
                # using kwargs by itself (usually it only contains a "pk" key
                # and this will work fine.
                lookup_kwargs = kwargs

            try:
                bundle.obj = self.obj_get(request, **lookup_kwargs)
            except ObjectDoesNotExist:
                raise NotFound("A model instance matching the provided arguments could not be found.")

        bundle = self.full_hydrate(bundle)

        # Save FKs just in case.
        self.save_related(bundle)

        # Save the main object.
        bundle.obj.save(priority=200, user=request.user if request else None)

        # Now pick up the M2M bits.
        m2m_bundle = self.hydrate_m2m(bundle)
        self.save_m2m(m2m_bundle)
        return bundle

    def save_related(self, bundle, request=None):
        """
        TAKEN FROM tastypie 0.9.11

        Handles the saving of related non-M2M data.

        Calling assigning ``child.parent = parent`` & then calling
        ``Child.save`` isn't good enough to make sure the ``parent``
        is saved.

        To get around this, we go through all our related fields &
        call ``save`` on them if they have related, non-M2M data.
        M2M data is handled by the ``ModelResource.save_m2m`` method.
        """
        from tastypie.resources import ObjectDoesNotExist
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_related', False):
                continue

            if getattr(field_object, 'is_m2m', False):
                continue

            if not field_object.attribute:
                continue

            if field_object.blank:
                continue

            # Get the object.
            try:
                related_obj = getattr(bundle.obj, field_object.attribute)
            except ObjectDoesNotExist:
                related_obj = None

            # Because sometimes it's ``None`` & that's OK.
            if related_obj:
                related_obj.save(priority=200, user=request.user if request else None)
                setattr(bundle.obj, field_object.attribute, related_obj)

    def save_m2m(self, bundle, request=None):
        """
        TAKEN FROM tastypie 0.9.11

        Handles the saving of related M2M data.

        Due to the way Django works, the M2M data must be handled after the
        main instance, which is why this isn't a part of the main ``save`` bits.

        Currently slightly inefficient in that it will clear out the whole
        relation and recreate the related data as needed.
        """
        for field_name, field_object in self.fields.items():
            if not getattr(field_object, 'is_m2m', False):
                continue

            if not field_object.attribute:
                continue

            if field_object.readonly:
                continue

            # Get the manager.
            related_mngr = getattr(bundle.obj, field_object.attribute)

            if hasattr(related_mngr, 'clear'):
                # Clear it out, just to be safe.
                related_mngr.clear()

            related_objs = []

            for related_bundle in bundle.data[field_name]:
                related_bundle.obj.save(priority=200, user=request.user if request else None)
                related_objs.append(related_bundle.obj)

            related_mngr.add(*related_objs)


class PhysicalServerResource(DeviceResource):
    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(model__type__in={
            DeviceType.rack_server.id, DeviceType.blade_server.id})
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class RackServerResource(DeviceResource):
    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(model__type=
            DeviceType.rack_server.id)
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class BladeServerResource(DeviceResource):
    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(model__type=
            DeviceType.blade_server.id)
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class VirtualServerResource(DeviceResource):
    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(model__type=
            DeviceType.virtual_server.id)
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class DevResource(DeviceResource):
    class Meta(DeviceResource.Meta):
        queryset = Device.objects.all()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


class IPAddressResource(MResource):
    device = fields.ForeignKey('ralph.discovery.api.DevResource', 'device',
        null=True)

    class Meta:
        queryset = IPAddress.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {
            'address': ALL,
            'hostname': ALL,
            'snmp_community': ALL,
            'device': ALL,
            'is_management': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority', 'dns_info',
            'snmp_name')
        cache = SimpleCache()
        throttle = CacheThrottle(throttle_at=THROTTLE_AT, timeframe=TIMEFREME,
                                expiration=EXPIRATION)


