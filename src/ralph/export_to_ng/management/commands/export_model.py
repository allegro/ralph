#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.management.base import BaseCommand, CommandError

#TODO:: make it from models
POSSIBLE_MODELS = """
Models independent:
AssetLastHostname
Environment
Service
Manufacture
+Category
ComponentModel
Warehouse
DataCenter
Accessory
Database
VIP
VirtualServer
CloudProject
LicenceType
SoftwareCategory ile
SupportType

Custom resoruces models:
+ralph.assets.models.assets.AssetModel
ralph.assets.models.components.GenericComponent
ralph.back_office.models.BackOfficeAsset
ralph.data_center.models.physical.ServerRoom
ralph.data_center.models.physical.Rack
ralph.data_center.models.physical.DataCenterAsset
ralph.data_center.models.physical.Connection
ralph.data_center.models.components.DiskShare
ralph.data_center.models.components.DiskShareMount
ralph.licences.models.Licence
ralph.supports.models.Support

ManyToMany Models:
ralph.assets.models.assets.ServiceEnvironment
    - service,
    - environment
ralph.licences.models.LicenceAsset
    - licence
    - asset
ralph.licences.models.LicenceUser
    - licence
    - user
ralph.data_center.models.physical.RackAccessory
    - accessory
    - rack
"""

import os
from import_export import resources
from ralph.export_to_ng import resources as ralph_resources
from django.db.models import get_models
import ralph_assets
APP_MODELS = {model._meta.object_name: model for model in get_models()}
APP_MODELS.update({
    # exceptions for ambigious models like Warehouse, which is in Scrooge and in
    # Assets, we need only asset's one so code below:
    'Warehouse': ralph_assets.models.Warehouse
})
def get_resource(model_name):
    """Return resource for import model."""
    resource_name = model_name + 'Resource'
    resource = getattr(ralph_resources, resource_name, None)
    if not resource:
        model_class = APP_MODELS[model_name]
        resource = resources.modelresource_factory(model=model_class)
    return resource()



from optparse import make_option
class Command(BaseCommand):
    help = os.linesep.join([
        'Export data in Ralph-NG format.',
        os.linesep,
        'Possible models to export:',
        POSSIBLE_MODELS,
    ])

    option_list = BaseCommand.option_list + (
        make_option(
            '--model_name',
            #action='store_true',
            #dest='delete',
            #default=False,
            help='The model name up to export (type "ralph export_to_ng -h" for possible models)',
        ),
        make_option(
            '--data_file',
            #action='store_true',
            #dest='delete',
            #default=False,
            help='CSV file name'
        ),
    )

    def handle(self, *args, **options):
        #self.stdout.write('Successfully closed poll "%s"\n' % poll_id)
        #raise CommandError('Poll "%s" does not exist' % poll_id)
        #import ipdb; ipdb.set_trace()
        model_resource = get_resource(options['model_name'])
        #queryset = model_resource._meta.model.objects.all()[:1]
        #dataset = model_resource.export(queryset=queryset)
        dataset = model_resource.export()
        with open(options['data_file'], 'wb') as output:
            output.write(dataset.csv)
