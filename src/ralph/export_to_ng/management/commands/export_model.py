#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import tempfile
from optparse import make_option
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.db.models import get_models
from import_export import resources

import ralph_assets
from ralph.discovery import models_device
from ralph.export_to_ng import resources as ralph_resources

ZIP_EXT = '.zip'
NAMESPACE_SIZE = 10
SIMPLE_MODELS = [
    'AssetLastHostname',
    'Environment',
    'Service',
    'Manufacturer',
    'Category',
    # mainly trash data: 'ComponentModel',
    'Warehouse',
    'DataCenter',
    'Accessory',
    # TODO: 'CloudProject',
    'LicenceType',
    'SoftwareCategory',
    'SupportType',
    # TODO: Database
    # TODO: VIP
    # TODO: VirtualServer
]
DEPENDENT_MODELS = [
    'AssetModel',
    # new scan handles that: 'GenericComponent',
    # 'BackOfficeAsset',
    'ServerRoom',
    'Rack',
    'DataCenterAsset',
    # new scan handles that: 'Connection',
    # new scan handles that: 'DiskShare',
    # new scan handles that: 'DiskShareMount',
    # 'Licence',
    # 'Support',
]
MANY_TO_MANY = [
    'ServiceEnvironment',
    # 'LicenceAsset',
    # 'LicenceUser',
    'RackAccessory',
]

ALLOWED_MODELS_MSG = """
Possible models to export are:

Simple models:
{}

Dependent models:
{}

ManyToMany Models:
{}
""".format(
    os.linesep.join(SIMPLE_MODELS),
    os.linesep.join(DEPENDENT_MODELS),
    os.linesep.join(MANY_TO_MANY),
)

APP_MODELS = {model._meta.object_name: model for model in get_models()}
APP_MODELS.update({
    # exceptions for ambigious models like Warehouse, which is in Scrooge and in
    # Assets, we need only asset's one so code below:
    'DataCenter': ralph_assets.models_dc_assets.DataCenter,
    'Warehouse': ralph_assets.models.Warehouse,
    'Service': models_device.ServiceCatalog,
})


def get_resource(model_name):
    """Return resource for import model."""
    resource_name = model_name + 'Resource'
    resource = getattr(ralph_resources, resource_name, None)
    if not resource:
        model_class = APP_MODELS[model_name]
        resource = resources.modelresource_factory(model=model_class)
    return resource()


class Command(BaseCommand):
    help = os.linesep.join([
        'Export data in Ralph-NG format.',
        ALLOWED_MODELS_MSG,
    ])
    option_list = BaseCommand.option_list + (
        make_option(
            '-z', '--zipfile',
            help='Path to zipped file where exported models should be stored',
        ),
    )

    def handle(self, *args, **options):
        models = args
        if not models:
            models = SIMPLE_MODELS + DEPENDENT_MODELS + MANY_TO_MANY

        filename = options['zipfile']
        if not filename.endswith(ZIP_EXT):
            filename += ZIP_EXT
        with ZipFile(filename, 'w') as zipped:
            dirpath = tempfile.mkdtemp()
            os.chdir(dirpath)
            for idx, model in enumerate(models, 1):
                self.stdout.write('Processing model {}\n'.format(model))

                model_resource = get_resource(model)
                dataset = model_resource.export()
                output_filename = "{}_{}.{}".format(
                    idx * NAMESPACE_SIZE, model, 'csv'
                )
                with open(output_filename, 'wb') as output_file:
                    output_file.write(dataset.csv)
                zipped.write(output_filename.encode('utf8'))
