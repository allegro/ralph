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

from django.contrib.contenttypes.models import ContentType
import logging
logger = logging.getLogger(__name__)

import ralph.discovery.models as db
import ralph.discovery.models_network as ndb
import ralph.business.models as bdb
import ralph.cmdb.models as cdb
from django.db import IntegrityError
from lck.django.common import nested_commit_on_success

class UnknownCTException(Exception):
    def __init__(self, value):
        Exception.__init__(self, value)
        self.parameter = value

    def __str__(self):
        return repr("Unknown content type : %s" % self.parameter)

class CIImporter(object):
    def __init__(self):
        # initial check for removed cis
        self.remove_moved_cis()

    @nested_commit_on_success
    def store_asset(self, asset, type_, layer_id, uid_prefix):
        """Store given asset as  CI  """
        logger.debug('Saving: %s' % asset)
        layer = cdb.CILayer.objects.get(id=layer_id)
        ci = cdb.CI()
        ci.uid = '%s-%s' % (uid_prefix, asset.id)
        ci.content_object = asset
        ci.type_id = type_
        ci.barcode = getattr(asset, 'barcode', None)
        ci.name = '%s' % asset.name or unicode(asset)
        try:
            # new CI
            ci.save()
            ci.layers = [layer]
        except IntegrityError:
            # Integrity error - existing CI Already in database.
            # Get CI by uid, and use it for saving data.
            ci = cdb.CI.get_by_content_object(asset)
        ci.save()
        return ci

    def remove_moved_cis(self):
        """
        Some CI has missing assets.
        This is the case, when Ralph deletes Asset(remove and re-add
        with different ID)

        CMDB has fixed uid relations schema, so CI has to be removed and
        added again.
        This is temporary bugfix, until Ralph fixed floating CI problem.
        All CI related information are lost, though.
        """
        logger.debug('Analysing CIs with missing asset')
        for x in cdb.CI.objects.all():
            if x.content_type and x.object_id and (not x.content_object):
                # id has changed
                logger.debug('Delete CI %s with missing asset.' % x)
                x.delete()

    def import_assets_by_contenttype(self, asset_class,
            _type, layer_id, asset_id=None):
        ret=[]
        logger.info('Importing devices.')
        asset_content_type = ContentType.objects.get_for_model(asset_class)
        prefix = cdb.CIContentTypePrefix.objects.filter(
                content_type_name=asset_content_type.app_label \
                        + '.' \
                + asset_content_type.model.replace(' ','')
        )
        if not prefix:
            raise TypeError('Unknown prefix for Content Type %s' \
                    % asset_content_type.app_label + '.' +  \
                    asset_content_type.model)
        uid_prefix=prefix[0].prefix
        if asset_id:
            all_devices = asset_class.objects.filter(
                    id=asset_id).order_by('id').all()
        else:
            all_devices = asset_class.objects.order_by('id').all()
        for d in all_devices:
            ret.append(self.store_asset(d, _type, layer_id, uid_prefix))
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
        """ Importing relations parent/child from Ralph  """
        content_id = content_type.id
        self.cache_content_types()
        if asset_id!=None:
            all_ciis = cdb.CI.objects.filter(
                    object_id=asset_id,
                    content_type_id=content_id,
            ).order_by('id').all()
        else:
            all_ciis = cdb.CI.objects.filter(
                    content_type_id=content_id,
            ).order_by('id').all()
        for d in all_ciis:
            obj = d.content_object
            try:
                if content_type == self.network_content_type:
                    self.import_network_relations(network=d,
                    )
                elif content_type == self.device_content_type:
                    self.import_device_relations(obj=obj, d=d)
                elif content_type == self.venture_content_type:
                    self.import_venture_relations(obj=obj, d=d)
                elif content_type == self.venture_role_content_type:
                    self.import_role_relations(obj=obj, d=d)
                elif content_type == self.datacenter_content_type:
                    # top level Ci without parent relations.
                    pass
                elif content_type == self.service_content_type:
                    self.import_service_relations(obj=obj, d=d)
                else:
                    raise UnknownCTException(content_type)
            except IntegrityError:
                pass


    @nested_commit_on_success
    def import_service_relations(self, obj, d):
        if obj.business_line:
            bline = cdb.CI.objects.get(
                    content_type=self.business_line_content_type,
                    name=obj.business_line,
            )
            cir = cdb.CIRelation()
            cir.parent = bline
            cir.child = d
            cir.readonly = True
            cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
            cir.save()

    @nested_commit_on_success
    def import_venture_relations(self, obj, d):
        """ Must be called after datacenter """
        if obj.data_center_id:
                datacenter_ci = cdb.CI.objects.filter(
                        content_type=self.datacenter_content_type,
                        object_id=obj.data_center_id).all()[0]
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = datacenter_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.REQUIRES.id
                try:
                    cir.save()
                except IntegrityError:
                    pass

        if obj.parent:
                logger.info('Saving relation: %s' % obj)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.child = d
                cir.parent = cdb.CI.objects.filter(
                        content_type_id=self.venture_content_type,
                        object_id=obj.parent.id)[0]
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                try:
                    cir.save()
                except IntegrityError:
                    pass

    @nested_commit_on_success
    def import_role_relations(self, obj, d):
        if obj.venture_id:
                # first venturerole in hierarchy, connect it to venture
                venture_ci = cdb.CI.objects.get(
                        content_type=self.venture_content_type,
                        object_id=obj.venture_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.HASROLE.id
                try:
                    cir.save()
                except IntegrityError:
                    pass
        if obj.parent:
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.child = d
                cir.parent = cdb.CI.objects.filter(
                        content_type_id=self.venture_role_content_type,
                        object_id=obj.parent.id)[0]
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                try:
                    cir.save()
                except IntegrityError:
                    pass

    @nested_commit_on_success
    def import_device_relations(self, obj, d):
        """ Must be called after ventures """
        for x in cdb.CIRelation.objects.filter(
                child=d,
                readonly=True):
            x.delete()
        if obj.venture_id and not obj.parent:
                venture_ci = cdb.CI.objects.get(
                        content_type=self.venture_content_type,
                        object_id=obj.venture_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                try:
                    cir.save()
                except IntegrityError:
                    pass

        if obj.venture_role_id and not obj.parent:
                venture_role_ci = cdb.CI.objects.get(
                        content_type=self.venture_role_content_type,
                        object_id=obj.venture_role_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_role_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.HASROLE.id
                try:
                    cir.save()
                except IntegrityError:
                    pass


        if obj.parent:
            logger.info('Saving relation: %s' % obj)
            cir = cdb.CIRelation()
            cir.readonly = True
            cir.child = d
            cir.parent = cdb.CI.objects.get(
                    content_type=self.device_content_type,
                    object_id=obj.parent.id)
            cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
            try:
                cir.save()
            except IntegrityError:
                pass

    @nested_commit_on_success
    def import_network_relations(self, network):
        """ Must be called after device_relations! """
        """ Make relations using network->ipaddresses->device """
        for ip in ndb.IPAddress.objects.filter(
                device__isnull=False,
                network=network.content_object).all():
            # make relations network->device
            ci_device = cdb.CI.objects.get(
                    content_type=self.device_content_type,
                    object_id=ip.device.id,
            )
            cir = cdb.CIRelation()
            cir.readonly = True
            cir.parent = network
            cir.child = ci_device
            cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
            try:
                cir.save()
            except IntegrityError:
                pass

    def import_single_object_relations(self, content_object):
        """
        Fasade for single Asset
        """
        ct = ContentType.objects.get_for_model(content_object)
        object_id = content_object.id
        return self.import_relations(ct, asset_id=object_id)


    def import_single_object(self, content_object):
        """
        Fasade for single Asset
        """
        ct = ContentType.objects.get_for_model(content_object)
        object_id=content_object.id
        return self.import_all_ci([ct], asset_id=object_id)

    def import_all_ci(self, content_types, asset_id=None):
        ret=[]
        content_to_import={
                db.Device: cdb.CI_TYPES.DEVICE.id,
                bdb.Venture: cdb.CI_TYPES.VENTURE.id,
                bdb.VentureRole: cdb.CI_TYPES.VENTUREROLE.id,
                ndb.Network: cdb.CI_TYPES.NETWORK.id,
                ndb.NetworkTerminator: cdb.CI_TYPES.NETWORKTERMINATOR.id,
                db.DataCenter: cdb.CI_TYPES.DATACENTER.id,
                bdb.Service : cdb.CI_TYPES.SERVICE.id,
                bdb.BusinessLine : cdb.CI_TYPES.BUSINESSLINE.id,
        }
        layers={
                db.Device: 5,
                bdb.Venture: 4,
                bdb.VentureRole: 8,
                ndb.Network:  6,
                ndb.NetworkTerminator: 6,
                db.DataCenter: 5,
                bdb.BusinessLine: 7,
                bdb.Service: 7,
        }
        for i in content_types:
            assetClass  = i.model_class()
            assetContentType = i
            logger.info('Importing content type : %s' % assetContentType)
            type_ = content_to_import[assetClass]
            layer = layers[assetClass]
            ret.extend(self.import_assets_by_contenttype(assetClass, type_, layer, asset_id))
        return ret

