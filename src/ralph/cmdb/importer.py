#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initial importing data(CI/Relation) from Ralph.
Relations are made explicit from data tables (parent_id).
________________________________________________________
CI and relations structure is described below:



                                Layer 1:                    Layer 2:
                                Network                     Ventures
 Ci4 = "IP Pool (...)"|      .____________ .             .____________.
 CI5 = "Allegro Prod" |     /   Ci1       /             /   Ci2       /
 r = requires         |    /   /c  \     /             /   /c  \     /
 c = contains         |   /   Ci3  Ci4<-/---- r ------/-->Ci5   Ci6 /
                      |   \____________/              \____________/



1. CI's - configuration Item (every object in ralph db)

2. Relations

Relation affects 2 CI's from
-> same layer
or
-> different layer

3. Layers
CI's are organized - assigned to different layers(Network, Ventures ...)

4. One CI can be assigned to one or more layers


"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
os.environ['DJANGO_SETTINGS_MODULE'] = "ralph.settings"

import logging
logger = logging.getLogger(__name__)

from django.contrib.contenttypes.models import ContentType

import ralph.discovery.models as db
import ralph.discovery.models_network as ndb
import ralph.business.models as bdb
import ralph.cmdb.models as cdb
from django.db import IntegrityError
from lck.django.common import nested_commit_on_success


def get_layers_for_ci_type(ci_type_id):
    try:
        ci_type = cdb.CIType.objects.get(pk=ci_type_id)
    except cdb.CIType.DoesNotExist:
        return
    return ci_type.cilayer_set.all()


class UnknownCTException(Exception):

    def __init__(self, value):
        Exception.__init__(self, value)
        self.parameter = value

    def __str__(self):
        return repr("Unknown content type : %s" % self.parameter)


def _create_or_update_relation(parent, child, relation_type):
    ci_relation, created = cdb.CIRelation.concurrent_get_or_create(
        parent=parent,
        child=child,
        type=relation_type,
        defaults={
            'readonly': True,
        },
    )
    if not created and not ci_relation.readonly:
        ci_relation.readonly = True
        ci_relation.save()
    return ci_relation


def _replace_relations(obj, ci, side, field, other_ct, relation_type):
    """A generic function replacing relations.
    :param obj: an object from ralph
    :param ci: a CI that reflects the object
    :param side: whether it should be a child or parent of relation
    :param other_ct: the content-type from other side
    :relateion_type: the type of CIRelations
    """
    used_relations = set()
    if getattr(obj, field):
        try:
            other = cdb.CI.objects.get(
                content_type=other_ct,
                object_id=getattr(obj, field).id,
            )
            kwargs = {'relation_type': relation_type}
            if side == 'child':
                kwargs['child'] = ci
                kwargs['parent'] = other
            else:
                kwargs['parent'] = ci
                kwargs['child'] = other
            used_relations.add(_create_or_update_relation(**kwargs).id)
        except cdb.CI.DoesNotExist:
            pass
    kwargs = {'type': relation_type}
    if side == 'child':
        kwargs['child'] = ci
        kwargs['parent__content_type'] = other_ct
    else:
        kwargs['parent'] = ci
        kwargs['child__content_type'] = other_ct
    cdb.CIRelation.objects.filter(**kwargs).exclude(
        id__in=used_relations
    ).delete()


class CIImporter(object):

    @nested_commit_on_success
    def store_asset(self, asset, type_, layers, uid_prefix):
        """Store given asset as  CI"""
        logger.debug('Saving: %s' % asset)
        ci = cdb.CI()
        ci.uid = '%s-%s' % (uid_prefix, asset.id)
        ci.content_object = asset
        ci.type_id = type_
        try:
            # new CI
            ci.save()
            ci.layers = layers
        except IntegrityError:
            # Integrity error - existing CI Already in database.
            # Get CI by uid, and use it for saving data.
            ci = cdb.CI.get_by_content_object(asset)
        ci.name = '%s' % asset.name or unicode(asset)
        if 'barcode' in asset.__dict__.keys():
            ci.barcode = asset.barcode
        if isinstance(asset, db.Device):
            active = not asset.deleted
        else:
            active = True
        ci.state = (
            cdb.CI_STATE_TYPES.ACTIVE if active
            else cdb.CI_STATE_TYPES.INACTIVE
        )
        ci.save()
        return ci

    def import_assets_by_contenttype(self, asset_class, _type, layers,
                                     asset_id=None):
        ret = []
        logger.info('Importing devices.')
        asset_content_type = ContentType.objects.get_for_model(asset_class)
        prefix = cdb.CIContentTypePrefix.objects.filter(
            content_type_name=asset_content_type.app_label + '.'
            + asset_content_type.model.replace(' ', '')
        )
        if not prefix:
            raise TypeError(
                'Unknown prefix for Content Type %s'
                % asset_content_type.app_label + '.' + asset_content_type.model
            )
        uid_prefix = prefix[0].prefix
        if issubclass(asset_class, db.Device):
            attr = 'admin_objects'
        else:
            attr = 'objects'
        if asset_id:
            all_devices = getattr(asset_class, attr).filter(
                id=asset_id).order_by('id').all()
        else:
            all_devices = getattr(asset_class, attr).order_by('id').all()
        for d in all_devices:
            ret.append(self.store_asset(d, _type, layers, uid_prefix))
        logger.info('Finished.')
        return ret

    def purge_all_ci(self, content_type=None):
        logger.info('Purging CIs')
        if content_type:
            for x in cdb.CI.objects.filter(
                    content_type__in=content_type).all().iterator():
                x.delete()
        else:
            # very very slow.
            for x in cdb.CI.objects.all().iterator():
                x.delete()

    def purge_all_relations(self):
        logger.info('Puring Relations')
        for x in cdb.CIRelation.objects.all().iterator():
            x.delete()

    def purge_system_relations(self):
        logger.info('Purging relations')
        for x in cdb.CIRelation.objects.filter(readonly=True).iterator():
            x.delete()

    def purge_user_relations(self):
        logger.info('Purging relations')
        for x in cdb.CIRelation.objects.filter(readonly=False).iterator():
            x.delete()

    def cache_content_types(self):
        self.venture_content_type = ContentType.objects.get(
            app_label='business',
            model='venture',
        )
        self.venture_role_content_type = ContentType.objects.get(
            app_label='business',
            model='venturerole',
        )
        self.datacenter_content_type = ContentType.objects.get(
            app_label='discovery',
            model='datacenter',
        )
        self.network_content_type = ContentType.objects.get(
            app_label='discovery',
            model='network',
        )
        self.device_content_type = ContentType.objects.get(
            app_label='discovery',
            model='device',
        )
        self.service_content_type = ContentType.objects.get(
            app_label='business',
            model='service',
        )
        self.business_line_content_type = ContentType.objects.get(
            app_label='business',
            model='businessline',
        )

    def import_relations(self, content_type, asset_id=None):
        """ Importing relations parent/child from Ralph """
        self.cache_content_types()
        additional_params = {}
        if asset_id is not None:
            additional_params['object_id'] = asset_id
        for ci in cdb.CI.objects.filter(
            content_type=content_type,
            **additional_params
        ).order_by('id'):
            obj = ci.content_object
            if content_type == self.network_content_type:
                self.import_network_relations(
                    network=ci,
                )
            elif content_type == self.device_content_type:
                self.import_device_relations(
                    obj=obj,
                    ci=ci,
                )
            elif content_type == self.venture_content_type:
                self.import_venture_relations(
                    obj=obj,
                    ci=ci,
                )
            elif content_type == self.venture_role_content_type:
                self.import_role_relations(
                    obj=obj,
                    ci=ci,
                )
            elif content_type == self.business_line_content_type:
                # top level Ci without parent relations.
                pass
            elif content_type == self.datacenter_content_type:
                # top level Ci without parent relations.
                pass
            elif content_type == self.service_content_type:
                self.import_service_relations(
                    obj=obj,
                    ci=ci,
                )
            else:
                raise UnknownCTException(content_type)

    @nested_commit_on_success
    def import_service_relations(self, obj, ci):
        # Special case because business lines are bound by name
        used_relations = set()
        if obj.business_line:
            try:
                bline = cdb.CI.objects.get(
                    content_type=self.business_line_content_type,
                    name=obj.business_line,
                )
                used_relations.add(_create_or_update_relation(
                    parent=bline,
                    child=ci,
                    relation_type=cdb.CI_RELATION_TYPES.CONTAINS,
                ).id)
            except cdb.CI.DoesNotExist:
                pass
        cdb.CIRelation.objects.filter(
            child=ci,
            parent__content_type=self.business_line_content_type,
            type=cdb.CI_RELATION_TYPES.CONTAINS,
        ).exclude(id__in=used_relations).delete()

    @nested_commit_on_success
    def import_venture_relations(self, obj, ci):
        """ Must be called after datacenter """
        _replace_relations(
            obj, ci, 'child', 'data_center',
            self.datacenter_content_type, cdb.CI_RELATION_TYPES.REQUIRES,
        )
        _replace_relations(
            obj, ci, 'child', 'parent',
            self.venture_content_type, cdb.CI_RELATION_TYPES.CONTAINS,
        )

    @nested_commit_on_success
    def import_role_relations(self, obj, ci):
        pass
        _replace_relations(
            obj, ci, 'child', 'venture',
            self.venture_content_type, cdb.CI_RELATION_TYPES.HASROLE,
        )
        _replace_relations(
            obj, ci, 'child', 'parent',
            self.venture_role_content_type, cdb.CI_RELATION_TYPES.CONTAINS,
        )

    @nested_commit_on_success
    def import_device_relations(self, obj, ci):
        """ Must be called after ventures """
        _replace_relations(
            obj, ci, 'child', 'venture',
            self.venture_content_type, cdb.CI_RELATION_TYPES.CONTAINS,
        )
        _replace_relations(
            obj, ci, 'child', 'venture_role',
            self.venture_role_content_type, cdb.CI_RELATION_TYPES.HASROLE
        )
        _replace_relations(
            obj, ci, 'child', 'parent',
            self.device_content_type, cdb.CI_RELATION_TYPES.CONTAINS
        )

    @nested_commit_on_success
    def import_network_relations(self, network):
        """
        Must be called after device_relations!
        Make relations using network->ipaddresses->device
        """
        used_relations = set()
        for ip in ndb.IPAddress.objects.filter(
            device__isnull=False,
            network=network.content_object,
        ).all():
            # make relations network->device
            try:
                ci_device = cdb.CI.objects.get(
                    content_type=self.device_content_type,
                    object_id=ip.device.id,
                )
                used_relations.add(_create_or_update_relation(
                    parent=network,
                    child=ci_device,
                    relation_type=cdb.CI_RELATION_TYPES.CONTAINS,
                ).id)
            except cdb.CI.DoesNotExist:
                pass
        cdb.CIRelation.objects.filter(
            parent=network,
            child__content_type=self.device_content_type,
            type=cdb.CI_RELATION_TYPES.CONTAINS,
        ).exclude(id__in=used_relations).delete()

    def import_single_object_relations(self, content_object):
        """Facade for single Asset"""
        ct = ContentType.objects.get_for_model(content_object)
        object_id = content_object.id
        return self.import_relations(ct, asset_id=object_id)

    def import_single_object(self, content_object):
        """Facade for single Asset"""
        ct = ContentType.objects.get_for_model(content_object)
        object_id = content_object.id
        return self.import_all_ci([ct], asset_id=object_id)

    def import_all_ci(self, content_types, asset_id=None):
        ret = []
        content_to_import = {
            db.Device: cdb.CI_TYPES.DEVICE.id,
            bdb.Venture: cdb.CI_TYPES.VENTURE.id,
            bdb.VentureRole: cdb.CI_TYPES.VENTUREROLE.id,
            ndb.Network: cdb.CI_TYPES.NETWORK.id,
            ndb.NetworkTerminator: cdb.CI_TYPES.NETWORKTERMINATOR.id,
            db.DataCenter: cdb.CI_TYPES.DATACENTER.id,
            bdb.Service: cdb.CI_TYPES.SERVICE.id,
            bdb.BusinessLine: cdb.CI_TYPES.BUSINESSLINE.id,
        }
        for i in content_types:
            assetClass = i.model_class()
            assetContentType = i
            logger.info('Importing content type : %s' % assetContentType)
            type_ = content_to_import[assetClass]
            layers = get_layers_for_ci_type(type_)
            ret.extend(self.import_assets_by_contenttype(
                assetClass, type_, layers, asset_id)
            )
        return ret

    def update_single_object(self, ci, instance):
        if ci.name != instance.name:
            ci.name = instance.name
            ci.save()
        elif hasattr(instance, 'barcode'):
            if ci.barcode != instance.barcode:
                ci.barcode = instance.barcode
                ci.save()
