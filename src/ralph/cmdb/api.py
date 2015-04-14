#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ReST CMDB API
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import operator

# Monkeypatch Tastypie
# fix in https://github.com/toastdriven/django-tastypie/pull/863
from ralph.cmdb.monkey import method_check
import tastypie
from tastypie.resources import Resource

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from tastypie.authentication import ApiKeyAuthentication
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.fields import ForeignKey as TastyForeignKey, ToOneField
from tastypie.resources import ModelResource as MResource
from tastypie.throttle import CacheThrottle
from tastypie.validation import Validation

from ralph.account.api_auth import RalphAuthorization
from ralph.account.models import Perm, Profile
from ralph.cmdb.models import (
    CI,
    CI_RELATION_TYPES,
    CIAttribute,
    CIAttributeValue,
    CIChange,
    CIChangeCMDBHistory,
    CIChangeGit,
    CIChangePuppet,
    CIChangeZabbixTrigger,
    CILayer,
    CIRelation,
    CIType,
)
from ralph.cmdb import models as db
from ralph.cmdb.models_ci import CIOwner, CIOwnershipType
from ralph.cmdb.util import breadth_first_search_ci, can_change_ci_state

Resource.method_check = method_check

THROTTLE_AT = settings.API_THROTTLING['throttle_at']
TIMEFRAME = settings.API_THROTTLING['timeframe']
EXPIRATION = settings.API_THROTTLING['expiration']


class BusinessLineResource(MResource):

    class Meta:
        # has only name, so skip content_object info
        queryset = CI.objects.filter(
            type__id=db.CI_TYPES.BUSINESSLINE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'added_manually': ALL,
            'barcode': ALL,
            'business_service': ALL,
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'name': ALL,
            'object_id': ALL,
            'pci_scope': ALL,
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_service': ALL,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'businessline'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class ServiceResource(MResource):

    class Meta:
        queryset = CI.objects.filter(type__id=db.CI_TYPES.SERVICE.id).all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'added_manually': ALL,
            'barcode': ALL,
            'business_service': ALL,
            'created': ALL,
            'modified': ALL,
            'name': ALL,
            'object_id': ALL,
            'pci_scope': ALL,
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_service': ALL,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'service'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle, **kwargs):
        # CMDB base info completed with content_object info
        attrs = (
            'external_key',
            'location',
            'it_person',
            'it_person_mail',
            'business_person',
            'business_person_mail',
            'business_line',
        )
        ci = bundle.obj
        for attr in attrs:
            bundle.data[attr] = getattr(ci.content_object, attr, '')
        return bundle


class CIRelationResource(MResource):

    class Meta:
        queryset = CIRelation.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'readonly': ALL,
            'resource_uri': ALL,
            'type': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cirelation'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle, **kwargs):
        cirelation = CIRelation.objects.get(pk=bundle.data.get('id'))
        bundle.data['parent'] = cirelation.parent.id
        bundle.data['child'] = cirelation.child.id
        return bundle


class OwnershipField(tastypie.fields.RelatedField):

    """A field representing a single type of owner relationship."""

    is_m2m = True

    def __init__(self, owner_type, effective=False, **kwargs):
        # Choices have broken deepcopy logic, so we can't store them
        self.owner_type = owner_type.id
        self.owner_type_name = owner_type.name
        self.effective = effective
        kwargs['readonly'] = self.effective
        args = (
            'ralph.cmdb.api.CIOwnersResource',
            self.get_attribute_name(),
        )
        super(OwnershipField, self).__init__(*args, **kwargs)

    def dehydrate(self, bundle, **kwargs):
        def get_owners(ci):
            owners = CIOwner.objects.filter(
                ciownership__type=self.owner_type,
                ciownership__ci=ci,
            )
            result = []
            for owner in owners:
                result.append(self.dehydrate_related(
                    bundle, self.get_related_resource(owner)
                ))
            return result
        if self.effective:
            found, result = breadth_first_search_ci(bundle.obj, get_owners)
            return result
        else:
            return get_owners(bundle.obj)

    def get_attribute_name(self):
        return '{0}_owners'.format(self.owner_type_name)

    def hydrate(self, bundle):
        pass

    def hydrate_m2m(self, bundle):
        if self.effective:
            return []
        owners_data = bundle.data[self.attribute]
        owners = [
            self.build_related_resource(data) for data in owners_data
        ]
        owner_dict = {owner.obj.pk: owner for owner in owners}
        return owner_dict.values()


class CustomAttributesField(tastypie.fields.ApiField):

    """The field that works on custom attributes of a CI."""

    is_m2m = True

    def __init__(self, *args, **kwargs):
        super(CustomAttributesField, self).__init__(*args, **kwargs)
        self.attribute = 'ciattributevalue_set'

    def dehydrate(self, bundle, **kwargs):
        ci = bundle.obj
        bundle.data['attributes'] = []
        result = []
        for attribute_value in ci.ciattributevalue_set.all():
            result.append({
                'name': attribute_value.attribute.name,
                'value': attribute_value.value,
            })
        return result

    def hydrate_m2m(self, bundle):
        ci = bundle.obj
        CIAttributeValue.objects.filter(ci=ci).delete()
        for attr_data in bundle.data.get('attributes', []):
            attribute = CIAttribute.objects.get(name=attr_data['name'])
            attribute_value = CIAttributeValue(
                ci=ci,
                attribute=attribute,
            )
            attribute_value.save()
            attribute_value.value = attr_data['value']
        return []

    def hydrate(self, bundle):
        pass


class LinkField(tastypie.fields.ApiField):

    """The field that provides some link based on the id of the resource."""

    readonly = True

    def __init__(self, view, as_qs, *args, **kwargs):
        self.view = view

        super(LinkField, self).__init__(*args, **kwargs)
        self.as_qs = as_qs

    def dehydrate(self, bundle, **kwargs):
        value = getattr(bundle.obj, 'id')
        if self.as_qs:
            return bundle.request.build_absolute_uri(
                reverse(self.view) + '?ci={0}'.format(value)
            )
        else:
            return bundle.request.build_absolute_uri(
                reverse(self.view, kwargs={'ci_id': value})
            )


class RelationField(tastypie.fields.ApiField):
    """The field that describes all relations of a given CI."""

    is_m2m = True
    dehydrated_type = 'related'

    def __init__(self, *args, **kwargs):
        super(RelationField, self).__init__(*args, **kwargs)
        self.attribute = lambda _: None

    def dehydrate(self, bundle, **kwargs):
        result = []
        id_ = bundle.obj.id
        for q, dir_name, other in (
            (Q(parent_id=id_), 'OUTGOING', 'child'),
            (Q(child_id=id_), 'INCOMING', 'parent'),
        ):
            for relation in CIRelation.objects.filter(q).select_related(other):
                other_ci = getattr(relation, other)
                result.append(
                    {
                        'type': CI_RELATION_TYPES.name_from_id(relation.type),
                        'dir': dir_name,
                        'id': other_ci.id,
                        'resource_uri': CIResourceV010(
                            api_name=self.api_name
                        ).get_resource_uri(other_ci),
                        'name': other_ci.name,
                        'ci_type': other_ci.type_id,
                    }
                )
        return result

    def hydrate_m2m(self, bundle):
        ci = bundle.obj
        CIRelation.objects.filter(
            Q(child_id=ci.id) | Q(parent_id=ci.id)
        ).delete()
        for relation_data in bundle.data.get('related', []):
            relation = CIRelation()
            try:
                type_id = CI_RELATION_TYPES.id_from_name(relation_data['type'])
            except ValueError:
                raise tastypie.exceptions.BadRequest(
                    'No such relation type {}'.format(relation_data['type'])
                )
            relation.type = type_id
            other_ci = CI.objects.get(id=relation_data['id'])
            if relation_data['dir'] == 'OUTGOING':
                relation.parent = ci
                relation.child = other_ci
            elif relation_data['dir'] == 'INCOMING':
                relation.parent = other_ci
                relation.child = ci
            else:
                raise tastypie.exceptions.BadRequest(
                    'dir should be OUTGOING or INCOMING'
                )
            relation.save()
        return []

    def hydrate(self, bundle):
        pass


class CIResourceValidation(Validation):

    def is_valid(self, bundle, request=None):
        errors = {}
        if not bundle.obj.pk:
            return errors
        try:
            ci = CI.objects.get(pk=bundle.obj.pk)
        except CI.DoesNotExist:
            return {'__all__': 'This object does not exist.'}
        changed_state = bundle.data.get('state')
        if not can_change_ci_state(ci, changed_state):
            message = """You can not change state because this service has
            linked devices."""
            errors['state'] = ' '.join(message.split())
        return errors


class CIResource(MResource):

    ci_link = LinkField(view='ci_view_main', as_qs=False)
    impact_link = LinkField(view='ci_graphs', as_qs=True)
    attributes = CustomAttributesField()
    business_owners = OwnershipField(CIOwnershipType.business, full=True)
    technical_owners = OwnershipField(CIOwnershipType.technical, full=True)
    effective_business_owners = OwnershipField(
        CIOwnershipType.business, full=True, effective=True
    )
    effective_technical_owners = OwnershipField(
        CIOwnershipType.technical, full=True, effective=True
    )
    layers = fields.ManyToManyField(
        'ralph.cmdb.api.CILayersResource', 'layers', full=True
    )
    type = TastyForeignKey(
        'ralph.cmdb.api.CITypesResource', 'type', full=True
    )

    class Meta:
        queryset = CI.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = [
            'get', 'post', 'put', 'patch', 'delete', 'head',
        ]
        resource_name = 'ci'
        filtering = {
            'attributes': ALL,
            'added_manually': ALL,
            'barcode': ('startswith', 'exact',),
            'business_service': ALL,
            'bussiness_owners': ALL,
            'cache_version': ALL,
            'created': ALL,
            'id': ALL,
            'layers': ALL_WITH_RELATIONS,
            'modified': ALL,
            'name': ('startswith', 'exact',),
            'object_id': ('exact',),
            'pci_scope': ('exact',),
            'resource_uri': ALL,
            'state': ALL,
            'status': ALL,
            'technical_owners': ALL,
            'technical_service': ALL,
            'type': ALL_WITH_RELATIONS,
            'uid': ALL,
            'zabbix_id': ALL,
        }
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )
        validation = CIResourceValidation()


class CIResourceV010(CIResource):
    """CIResource with related feature."""

    related = RelationField()

    def build_filters(self, filters=None):
        filters = filters or {}
        queries = []
        for qs_key, field in [
            ('child', 'parent__child__id'),
            ('parent', 'child__parent__id'),
        ]:
            for ci_id in filters.pop(qs_key, []):
                queries.append(Q(**{field: ci_id}))
        orm_filters = super(CIResourceV010, self).build_filters(filters)
        if queries:
            query = reduce(operator.and_, queries[1:], queries[0])
            cis = CI.objects.filter(query)
            orm_filters['pk__in'] = [ci.id for ci in cis]
        return orm_filters


class CILayersResource(MResource):

    class Meta:
        queryset = CILayer.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
            'resource_uri': ALL,
        }
        excludes = ('icon', )
        list_allowed_methods = ['get']
        resourse_name = 'cilayers'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeResource(MResource):

    class Meta:
        queryset = CIChange.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'created': ALL,
            'external_key': ALL,
            'id': ALL,
            'message': ALL,
            'modified': ALL,
            'object_id': ALL,
            'priority': ALL,
            'registration_type': ALL,
            'resource_uri': ALL,
            'time': ALL,
            'type': ALL,
        }
        excludes = ('cache_version', )
        allowed_methods = ['get']
        resource_name = 'cichange'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeZabbixTriggerResource(MResource):

    class Meta:
        queryset = CIChangeZabbixTrigger.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'comments': ALL,
            'created': ALL,
            'description': ALL,
            'host': ALL,
            'host_id': ALL,
            'id': ALL,
            'lastchange': ALL,
            'modified': ALL,
            'priority': ALL,
            'resource_uri': ALL,
            'status': ALL,
            'trigger_id': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangezabbixtrigger'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeGitResource(MResource):

    class Meta:
        queryset = CIChangeGit.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_git,
            ]
        )
        filtering = {
            'author': ALL,
            'changeset': ALL,
            'comment': ALL,
            'created': ALL,
            'file_paths': ALL,
            'id': ALL,
            'modified': ALL,
            'resource_uri': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangegit'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangePuppetResource(MResource):

    class Meta:
        queryset = CIChangePuppet.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_puppet,
            ]
        )
        filtering = {
            'configuration_version': ALL,
            'created': ALL,
            'host': ALL,
            'id': ALL,
            'kind': ALL,
            'modified': ALL,
            'resource_uri': ALL,
            'status': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get', 'post']
        resource_name = 'cichangepuppet'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIChangeCMDBHistoryResource(MResource):
    ci = TastyForeignKey(CIResource, 'ci')

    class Meta:
        queryset = CIChangeCMDBHistory.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'ci': ALL,
            'comment': ALL,
            'created': ALL,
            'field_name': ALL,
            'id': ALL,
            'modified': ALL,
            'new_value': ALL,
            'old_value': ALL,
            'resource_uri': ALL,
            'time': ALL,
        }
        excludes = ('cache_version', )
        list_allowed_methods = ['get']
        resource_name = 'cichangecmdbhistory'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CITypesResource(MResource):

    class Meta:
        queryset = CIType.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        filtering = {
            'id': ALL,
            'name': ALL,
            'resource_uri': ALL,
        }
        list_allowed_methods = ['get']
        resourse_name = 'citypes'
        excludes = ['cache_version', 'created', 'modified']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class UserResource(MResource):
    class Meta:
        queryset = User.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = ['get']
        filtering = {
            'first_name': ALL,
            'last_name': ALL,
            'username': ALL,
        }
        resource_name = 'users'
        excludes = ['password', 'last_login', 'is_staff', 'is_superuser']
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class ProfileResource(MResource):
    user = ToOneField(UserResource, 'user', full=True)

    class Meta:
        queryset = Profile.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = ['get']
        filtering = {
            'user': ALL_WITH_RELATIONS,
        }
        resource_name = 'profiles'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )


class CIOwnersResource(MResource):
    profile = ToOneField(ProfileResource, 'profile', full=True)

    class Meta:
        queryset = CIOwner.objects.all()
        authentication = ApiKeyAuthentication()
        authorization = RalphAuthorization(
            required_perms=[
                Perm.read_configuration_item_info_generic,
            ]
        )
        list_allowed_methods = ['get', 'post']
        filtering = {
            'cache_version': ALL,
            'created': ALL,
            'id': ALL,
            'modified': ALL,
            'resource_uri': ALL,
            'profile': ALL_WITH_RELATIONS,
        }
        excludes = ('cache_version', )
        resource_name = 'ciowners'
        throttle = CacheThrottle(
            throttle_at=THROTTLE_AT,
            timeframe=TIMEFRAME,
            expiration=EXPIRATION,
        )

    def dehydrate(self, bundle):
        for field in [
            'first_name',
            'last_name',
            'sAMAccountName',
            'email',
        ]:
            bundle.data[field] = getattr(bundle.obj, field)
        return bundle
