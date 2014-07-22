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

import datetime

from django.conf import settings
from django.db import models as db
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.cache import SimpleCache
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle

from ralph.account.api_auth import RalphAuthorization
from ralph.account.models import Perm
from ralph.discovery.models import (
    ComponentType,
    Device,
    DeviceModel,
    DeviceModelGroup,
    DeviceType,
    IPAddress,
    Network,
    NetworkKind,
)
from ralph.ui.views.common import _get_details

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']
SAVE_PRIORITY = 10


class IPAddressResource(MResource):
    device = fields.ForeignKey(
        'ralph.discovery.api.DevResource',
        'device',
        null=True,
    )
    network = fields.ForeignKey(
        'ralph.discovery.api.NetworksResource',
        'network',
        null=True,
    )
    venture = fields.ForeignKey(
        'ralph.business.api.VentureLightResource',
        'venture',
        null=True,
        full=True,
    )

    class Meta:
        queryset = IPAddress.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_network_structure,
            ]
        )
        filtering = {
            'address': ALL,
            'created': ALL,
            'device': ALL,
            'hostname': ALL,
            'http_family': ALL,
            'id': ALL,
            'is_management': ALL,
            'last_plugins': ALL,
            'last_puppet': ALL,
            'last_seen': ALL,
            'modified': ALL,
            'number': ALL,
            'snmp_community': ALL,
        }
        excludes = (
            'dns_info',
            'max_save_priority',
            'save_priorities',
            'snmp_name',
            'cache_version',
        )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle):
        if not self.fields.get('network'):
            return bundle
        try:
            network = self.fields['network'].fk_resource.instance
        except AttributeError:
            return bundle
        bundle.data['network_details'] = {
            'name': network.name if network else '',
            'address': network.address if network else '',
            'network_kind': (
                network.kind.name if network and network.kind else ''
            ),
        }
        return bundle


class ModelGroupResource(MResource):

    class Meta:
        queryset = DeviceModelGroup.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'created': ALL,
            'ip': ALL,
            'modified': ALL,
            'name': ALL,
            'price': ALL,
            'slots': ALL,
            'type': ALL,
        }
        excludes = (
            'cache_version',
        )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class ModelResource(MResource):
    group = fields.ForeignKey(
        ModelGroupResource,
        'group',
        null=True,
        full=True,
    )

    class Meta:
        queryset = DeviceModel.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        filtering = {
            'chassis_size': ALL,
            'created': ALL,
            'group': ALL,
            'id': ALL,
            'modified': ALL,
            'name': ALL,
        }
        excludes = ('save_priorities', 'max_save_priority', 'cache_version', )
        cache = SimpleCache()
        filtering = {
            'type': ALL,
        }
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class DeviceResource(MResource):
    model = fields.ForeignKey(ModelResource, 'model', null=True, full=True)
    management = fields.ForeignKey(
        IPAddressResource,
        'management',
        null=True,
        full=True,
    )
    venture = fields.ForeignKey(
        'ralph.business.api.VentureLightResource',
        'venture',
        null=True,
        full=True,
    )
    role = fields.ForeignKey(
        'ralph.business.api.RoleLightResource',
        'venture_role',
        null=True,
        full=True,
    )
    ip_addresses = fields.ToManyField(
        IPAddressResource,
        'ipaddress',
        related_name='device',
        full=True,
    )
    properties = fields.ToManyField(
        'ralph.business.api.RolePropertyValueResource',
        'rolepropertyvalue',
        related_name='device',
        full=True,
    )

    def dehydrate(self, bundle):
        properties = bundle.obj.get_property_set()
        bundle.data['properties_summary'] = properties
        return bundle

    class Meta:
        excludes = ('save_priorities', 'max_save_priority')
        filtering = {
            'barcode': ALL,
            'boot_firmware': ALL,
            'cached_cost': ALL,
            'cached_price': ALL,
            'chassis_position': ALL,
            'created': ALL,
            'dc': ALL,
            'deleted': ALL,
            'deprecation_date': ALL,
            'diag_firmware': ALL,
            'hard_firmware': ALL,
            'id': ALL,
            'ip_addresses': ALL_WITH_RELATIONS,
            'last_seen': ALL,
            'management': ALL,
            'mgmt_firmware': ALL,
            'model': ALL_WITH_RELATIONS,
            'modified': ALL,
            'name': ALL,
            'position': ALL,
            'price': ALL,
            'properties': ALL,
            'purchase_date': ALL,
            'rack': ALL,
            'remarks': ALL,
            'role': ALL_WITH_RELATIONS,
            'sn': ALL,
            'support_expiration_date': ALL,
            'support_kind': ALL,
            'uptime_seconds': ALL,
            'uptime_timestamp': ALL,
            'venture': ALL_WITH_RELATIONS,
            'verified': ALL,
            'warranty_expiration_date': ALL,
        }
        excludes = ('cache_version')
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_dc_structure,
            ]
        )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
        limit = 100

    def obj_update(self, bundle, request=None, **kwargs):
        """
        TAKEN FROM tastypie 0.9.11

        A ORM-specific implementation of ``obj_update``.
        """
        from tastypie.resources import NOT_AVAILABLE, ObjectDoesNotExist, NotFound
        if not bundle.obj or not bundle.obj.pk:
            # Attempt to hydrate data from kwargs before doing a lookup for the object.
            # This step is needed so certain values (like datetime) will pass
            # model validation.
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
                raise NotFound(
                    "A model instance matching the provided arguments could not be found.")

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
                related_obj.save(
                    priority=200,
                    user=request.user if request else None,
                )
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
                related_bundle.obj.save(
                    priority=200,
                    user=request.user if request else None,
                )
                related_objs.append(related_bundle.obj)

            related_mngr.add(*related_objs)


class PhysicalServerResource(DeviceResource):

    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(
            model__type__in={
                DeviceType.rack_server.id,
                DeviceType.blade_server.id,
            }
        )
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class RackServerResource(DeviceResource):

    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(
            model__type=DeviceType.rack_server.id,
        )
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class BladeServerResource(DeviceResource):

    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(
            model__type=DeviceType.blade_server.id,
        )
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class VirtualServerResource(DeviceResource):

    class Meta(DeviceResource.Meta):
        queryset = Device.objects.filter(
            model__type=DeviceType.virtual_server.id,
        )
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class DevResource(DeviceResource):

    class Meta(DeviceResource.Meta):
        queryset = Device.objects.all()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class DeviceWithPricingResource(DeviceResource):

    class Meta:
        queryset = Device.objects.all()
        resource_name = 'devicewithpricing'

    def dehydrate(self, bundle):
        device = bundle.obj
        details = _get_details(bundle.obj)
        components = dict()
        total = 0
        for detail in details:
            model = detail.get('model')
            price = detail.get('price') or 0
            model_type = None
            model_name = str(model)
            if hasattr(model, 'type'):
                try:
                    model_type = ComponentType.from_id(model.type)
                except ValueError:
                    pass
            if model_type and model_type == ComponentType.software:
                model = ComponentType.software.name,
                model_name = model
            if not components.get(model_name):
                components[model_name] = {
                    'model': model,
                    'count': 1,
                    'price': price,
                    'serial': detail.get('serial'),
                }
            else:
                components[model_name]['count'] += 1
            total += price
        bundle.data['components'] = components.values()
        bundle.data['total_cost'] = total
        bundle.data['deprecated'] = device.is_deprecated()
        splunk_start = bundle.request.GET.get('splunk_start')
        splunk_end = bundle.request.GET.get('splunk_end')
        if splunk_start and splunk_end:
            try:
                splunk_start = datetime.datetime.strptime(
                    splunk_start,
                    '%Y-%m-%d',
                )
                splunk_end = datetime.datetime.strptime(
                    splunk_end,
                    '%Y-%m-%d',
                )
            except ValueError:
                splunk_start, splunk_end = None, None
        splunk = self.splunk_cost(bundle.obj, splunk_start, splunk_end)
        bundle.data['splunk'] = splunk
        return bundle

    def splunk_cost(self, device, start_date=None, end_date=None):
        splunk_cost = {
            'splunk_size': 0,
            'splunk_monthly_cost': 0,
            'splunk_daily_cost': 0,
        }
        if start_date and end_date:
            splunk = device.splunkusage_set.filter(
                day__range=(start_date, end_date)
            ).order_by('-day')
        else:
            last_month = datetime.date.today() - datetime.timedelta(days=30)
            splunk = device.splunkusage_set.filter(
                day__gte=last_month
            ).order_by('-day')
        if splunk.count():
            splunk_size = splunk.aggregate(db.Sum('size'))['size__sum'] or 0
            splunk_monthly_cost = (
                splunk[0].get_price(size=splunk_size) /
                splunk[0].model.group.size_modifier
            ) or 0
            splunk_daily_cost = (splunk_monthly_cost / splunk.count()) or 0
            splunk_cost['splunk_size'] = splunk_size
            splunk_cost['splunk_monthly_cost'] = splunk_monthly_cost
            splunk_cost['splunk_daily_cost'] = splunk_daily_cost
        return splunk_cost


class NetworkKindsResource(MResource):

    class Meta:
        queryset = NetworkKind.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_network_structure,
            ]
        )
        filtering = {'name'}
        excludes = ('icon')
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class NetworksResource(MResource):
    network_kind = fields.ForeignKey(
        'ralph.discovery.api.NetworkKindsResource',
        'kind',
        null=True,
    )

    class Meta:
        queryset = Network.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_network_structure,
            ]
        )
        filtering = {
        }
        excludes = (
        )
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
