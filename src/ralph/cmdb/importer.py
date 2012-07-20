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
from django.utils.translation import ugettext
ugettext('Force initializing all apps by Django to prevent import cycles.')

from django.contrib.contenttypes.models import ContentType
import logging
logger = logging.getLogger(__name__)

import ralph.discovery.models as db
import ralph.discovery.models_network as ndb
import ralph.business.models as bdb
import ralph.cmdb.models as cdb
from django.db import IntegrityError

class UnknownCTException(Exception):
    pass

class CIImporter(object):
    @classmethod
    def store_asset(cls, asset, type_, layer_id, uid_prefix):
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

    @classmethod
    def import_assets_by_contenttype(cls, asset_class,
            _type, layer_id, asset_id=None):
        ret=[]
        logger.info('Importing devices.')
        asset_content_type = ContentType.objects.get_for_model(asset_class)
        prefix = cdb.CIContentTypePrefix.objects.filter(
                content_type_name=asset_content_type.app_label \
                        + '.' \
                + asset_content_type.model
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
            ret.append(cls.store_asset(d, _type, layer_id, uid_prefix))
        logger.info('Finished.')
        return ret

    @classmethod
    def purge_all_ci(cls, content_type=None):
        logger.info('Purging CIs')
        if content_type:
            for x in cdb.CI.objects.filter(
                    content_type__in=content_type).all().iterator():
                        x.delete()
        else:
            # very very slow.
            for x in cdb.CI.objects.all().iterator():
                x.delete()

    @classmethod
    def purge_all_relations(cls):
        logger.info('Puring Relations')
        for x in cdb.CIRelation.objects.all().iterator():
            x.delete()

    @classmethod
    def purge_system_relations(cls):
        logger.info('Purging relations')
        for x in cdb.CIRelation.objects.filter(readonly=True).iterator():
            x.delete()

    @classmethod
    def purge_user_relations(cls):
        logger.info('Purging relations')
        for x in cdb.CIRelation.objects.filter(readonly=False).iterator():
            x.delete()

    @classmethod
    def cache_content_types(cls):
        cls.venture_content_type = ContentType.objects.get(
                app_label='business',
                model='venture',
        )
        cls.venture_role_content_type = ContentType.objects.get(
                app_label='business',
                model='venturerole',
        )
        cls.datacenter_content_type = ContentType.objects.get(
                app_label='discovery',
                model='datacenter',
        )
        cls.network_content_type = ContentType.objects.get(
                app_label='discovery',
                model='network',
        )
        cls.device_content_type = ContentType.objects.get(
                    app_label='discovery',
                    model='device',
        )

    @classmethod
    def import_relations(cls, content_type, asset_id=None):
        """ Importing relations parent/child from Ralph  """
        content_id = content_type.id
        cls.cache_content_types()
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
            if content_type == cls.network_content_type:
                cls.import_network_relations(network=d,
                )
            elif content_type == cls.device_content_type:
                cls.import_device_relations(obj=obj, d=d)
            elif content_type == cls.venture_content_type:
                cls.import_venture_relations(obj=obj, d=d)
            elif content_type == cls.venture_role_content_type:
                cls.import_role_relations(obj=obj, d=d)
            else:
                raise UnknownCTException


    @classmethod
    def import_venture_relations(cls, obj, d):
        """ Must be called after datacenter """
        if obj.data_center_id:
                datacenter_ci = cdb.CI.objects.filter(
                        content_type=cls.datacenter_content_type,
                        object_id=obj.data_center_id).all()[0]
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = datacenter_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.REQUIRES.id
                cir.save()
        if obj.parent:
                logger.info('Saving relation: %s' % obj)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.child = d
                cir.parent = cdb.CI.objects.filter(
                        content_type_id=cls.venture_content_type,
                        object_id=obj.parent.id)[0]
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                cir.save()

    @classmethod
    def import_role_relations(cls, obj, d):
        if obj.venture_id:
                # first venturerole in hierarchy, connect it to venture
                venture_ci = cdb.CI.objects.get(
                        content_type=cls.venture_content_type,
                        object_id=obj.venture_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.HASROLE.id
                cir.save()
        if obj.parent:
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.child = d
                cir.parent = cdb.CI.objects.filter(
                        content_type_id=cls.venture_role_content_type,
                        object_id=obj.parent.id)[0]
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                cir.save()

    @classmethod
    def import_device_relations(cls, obj, d):
        """ Must be called after ventures """
        for x in cdb.CIRelation.objects.filter(
                child=d,
                readonly=True):
            x.delete()
        if obj.venture_id and not obj.parent:
                venture_ci = cdb.CI.objects.get(
                        content_type=cls.venture_content_type,
                        object_id=obj.venture_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
                cir.save()
        if obj.venture_role_id and not obj.parent:
                venture_role_ci = cdb.CI.objects.get(
                        content_type=cls.venture_role_content_type,
                        object_id=obj.venture_role_id)
                cir = cdb.CIRelation()
                cir.readonly = True
                cir.parent = venture_role_ci
                cir.child = d
                cir.type = cdb.CI_RELATION_TYPES.HASROLE.id
                cir.save()
        if obj.parent:
            logger.info('Saving relation: %s' % obj)
            cir = cdb.CIRelation()
            cir.readonly = True
            cir.child = d
            cir.parent = cdb.CI.objects.get(
                    content_type=cls.device_content_type,
                    object_id=obj.parent.id)
            cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
            cir.save()

    @classmethod
    def import_network_relations(cls, network):
        """ Must be called after device_relations! """
        """ Make relations using network->ipaddresses->device """
        for ip in ndb.IPAddress.objects.filter(
                device__isnull=False,
                network=network.content_object).all():
            # make relations network->device
            ci_device = cdb.CI.objects.get(
                    content_type=cls.device_content_type,
                    object_id=ip.device.id,
            )
            #remove old relations with networks only!
            for x in cdb.CIRelation.objects.filter(child=ci_device,
                    readonly=True,
                    parent__content_type_id=cls.network_content_type).all():
                x.delete()
            cir = cdb.CIRelation()
            cir.readonly = True
            cir.parent = network
            cir.child = ci_device
            cir.type = cdb.CI_RELATION_TYPES.CONTAINS.id
            cir.save()

    @classmethod
    def import_all_ci(cls, content_types, asset_id=None):
        ret=[]
        content_to_import={
                db.Device: cdb.CI_TYPES.DEVICE.id,
                bdb.Venture: cdb.CI_TYPES.VENTURE.id,
                bdb.VentureRole: cdb.CI_TYPES.VENTUREROLE.id,
                ndb.Network: cdb.CI_TYPES.NETWORK.id,
                ndb.NetworkTerminator: cdb.CI_TYPES.NETWORKTERMINATOR.id,
                db.DataCenter: cdb.CI_TYPES.DATACENTER.id,
        }
        layers={
                db.Device: 5,
                bdb.Venture: 4,
                bdb.VentureRole: 8,
                ndb.Network:  6,
                ndb.NetworkTerminator: 6,
                db.DataCenter: 5,
        }
        for i in content_types:
            assetClass  = i.model_class()
            assetContentType = i
            logger.info('Importing content type : %s' % assetContentType)
            type_ = content_to_import[assetClass]
            layer = layers[assetClass]
            ret.extend(cls.import_assets_by_contenttype(assetClass, type_, layer, asset_id))
        return ret

def importer_main():
    '''
    Warning. This command purges CMDB and makes CI/Relations from Ralph database.
    '''
    content_types = [
        ContentType.objects.get(app_label='discovery', model='device'),
        ContentType.objects.get(app_label='business', model='venture'),
        ContentType.objects.get(app_label='business', model='venturerole'),
        ContentType.objects.get(app_label='discovery', model='datacenter'),
        ContentType.objects.get(app_label='discovery', model='network'),
        ContentType.objects.get(app_label='discovery', model='networkterminator'),
    ]
    actions = ['purge','import']
    kinds = ['ci','user-relations','all-relations', 'system-relations']

    from optparse import OptionParser
    usage = "usage: %prog --action=[purge|import] \
            --kind=[ci/user-relations/all-relations/system-relations] \
            --content-types"
    parser = OptionParser(usage)
    parser.add_option('--action',
            dest='action',
            help="Purge all CI and Relations."
    )
    parser.add_option('--kind',
            dest='kind',
            help="Choose import kind.",
    )
    parser.add_option('--ids',
            dest='ids',
            help="Choose ids to import.",
    )
    parser.add_option('--content-types',
            dest='content_types',
            help="Type of content to reimport.",
            default=[],
    )
    (options, args) = parser.parse_args()
    if not options.action or options.action not in actions:
        parser.error("Specify valid action: " + ','.join(actions))
        return
    if not options.kind or options.kind not in kinds:
        parser.error("You must specify valid kind: " + '|'.join(kinds))
        return
    content_types_names = dict([ (x.app_label + '.' + x.model,x)
        for x in content_types ])
    content_types_to_import = []
    id_to_import = None
    if options.ids:
        id_to_import = int(options.ids)
    if options.content_types:
        t = options.content_types.split(',')
        for ct in t:
            if not content_types_names.get(ct,None):
                parser.error("Invalid content type: %s: " % ct)
            else:
                content_types_to_import.append(content_types_names.get(ct,None))
    else:
        content_types_to_import = content_types
    if raw_input('Are you sure, to reimport all data ? \
            All existing Ci/relations will be deleted. (y/n) >') != 'y':
        print('Aborted')
        return
    if options.action == 'purge':
        if options.kind == 'ci':
            CIImporter.purge_all_ci(content_types_to_import)
        elif options.kind == 'all-relations':
            CIImporter.purge_all_relations()
        elif options.kind == 'user-relations':
            CIImporter.purge_user_relations()
        elif options.kind == 'system-relations':
            CIImporter.purge_system_relations()
    elif options.action == 'import':
        if options.kind == 'ci':
            CIImporter.import_all_ci(content_types_to_import, id_to_import)
        elif options.kind == 'all-relations':
            for content_type in content_types_to_import:
                CIImporter.import_relations(content_type, id_to_import)
        else:
            parser.error("Invalid kind for this action")
    logger.info('Ready.')
