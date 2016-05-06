#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import tempfile
from optparse import make_option
from zipfile import ZipFile

from django.core.management.base import BaseCommand
from django.db.models import get_models
from import_export import resources
from ipaddr import AddressValueError, IPv4Network

import ralph_assets
from ralph.discovery import models_device
from ralph.export_to_ng import resources as ralph_resources

ZIP_EXT = '.zip'
NAMESPACE_SIZE = 10
SIMPLE_MODELS = [
    'AssetLastHostname',
    'AssetHolder',
    'Environment',
    'BusinessSegment',
    'ProfitCenter',
    'Service',
    'Manufacturer',
    'Category',
    # mainly trash data: 'ComponentModel',
    'Warehouse',
    'DataCenter',
    'DiscoveryDataCenter',
    'Accessory',
    # TODO: 'CloudProject',
    'LicenceType',
    'OfficeInfrastructure',
    'BudgetInfo',
    'Software',
    # TODO: Database
    # TODO: VIP
    # TODO: VirtualServer
    'NetworkKind',
    'NetworkEnvironment',
    'SupportType',
    'Region',
    'ConfigurationModule',
    'ConfigurationClass',
]
DEPENDENT_MODELS = [
    'ServiceEnvironment',
    'AssetModel',
    # new scan handles that: 'GenericComponent',
    'BackOfficeAsset',
    'ServerRoom',
    'Rack',
    'DataCenterAsset',
    # new scan handles that: 'Connection',
    # new scan handles that: 'DiskShare',
    # new scan handles that: 'DiskShareMount',
    'Licence',
    'Support',
    'Network',
    'IPAddress',
]
MANY_TO_MANY = [
    'BaseObjectLicence',
    'LicenceUser',
    'BaseObjectsSupport',
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
    # exceptions for ambigious models like Warehouse,
    # which is in Scrooge and in
    # Assets, we need only asset's one so code below:
    'DataCenter': ralph_assets.models_dc_assets.DataCenter,
    'Warehouse': ralph_assets.models.Warehouse,
    'Service': models_device.ServiceCatalog,
    'Software': ralph_assets.licences.models.SoftwareCategory,
    'OfficeInfrastructure': ralph_assets.models_assets.Service,
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
        make_option(
            '-e', '--exclude',
            help='Excluded models',
            action="append",
            type="str"
        ),
        make_option(
            '--exclude-network',
            action="append",
            help='Excludes network from address, eg.: --exclude-network=10.20.30.00/24',  # noqa
            type="str"
        ),
        make_option(
            '--exclude-empty-venture-role',
            action="store_true",
            help='Excludes ventures/roles without assigned devices',
        ),
    )

    def set_options_on_resource(self, model, options, model_resource):
        """Injects command line options to resources"""
        if model == 'Network' and options.get('exclude_network', None):
            excluded_networks = []
            for network in options['exclude_network']:
                try:
                    IPv4Network(network)
                except AddressValueError:
                    self.stdout.write(
                        "Value '{}' for '--exclude-network' is not CIDR format".format(  # noqa
                            network
                        )
                    )
                    sys.exit()
                excluded_networks.append(network)
            model_resource.excluded_networks = excluded_networks
        if (
            model in ('ConfigurationClass', 'ConfigurationModule') and
            options.get('exclude_empty_venture_role', False)
        ):
            model_resource.skip_empty = True
        return model_resource

    def handle(self, *args, **options):
        models = args
        if not models:
            models = SIMPLE_MODELS + DEPENDENT_MODELS + MANY_TO_MANY
        if options['exclude']:
            models = [m for m in models if m not in options['exclude']]
        filename = options['zipfile']
        if not filename.endswith(ZIP_EXT):
            filename += ZIP_EXT
        with ZipFile(filename, 'w') as zipped:
            dirpath = tempfile.mkdtemp()
            os.chdir(dirpath)
            for idx, model in enumerate(models, 1):
                self.stdout.write('Processing model {}\n'.format(model))

                model_resource = get_resource(model)
                model_resource = self.set_options_on_resource(
                    model, options, model_resource
                )
                dataset = model_resource.export()
                output_filename = "{}_{}.{}".format(
                    idx * NAMESPACE_SIZE, model, 'csv'
                )
                with open(output_filename, 'wb') as output_file:
                    output_file.write(dataset.csv)
                self.stdout.write('exported: {}\n'.format(len(dataset)))
                zipped.write(output_filename.encode('utf8'))
