# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import csv
import os
import six
import tablib


from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from import_export import resources
from ralph.data_importer import resources as ralph_resources
from ralph.data_importer.resources import DefaultResource
from six.moves import input


if six.PY2:
    from ralph.lib.unicode_csv import UnicodeReader as csv_reader
else:
    from csv import reader as csv_reader


APP_MODELS = {model._meta.model_name: model for model in apps.get_models()}


def get_resource(model_name):
    """Return resource for import model."""
    resource_name = model_name + 'Resource'
    resource = getattr(ralph_resources, resource_name, None)
    if not resource:
        model_class = APP_MODELS[model_name.lower()]
        resource = resources.modelresource_factory(
            model=model_class,
            resource_class=DefaultResource
        )
    return resource()


class Command(BaseCommand):

    help = "Imports data for specified model from specified file"

    def add_arguments(self, parser):
        parser.add_argument(
            'model_name',
            help='The model name to which the import data',
        )
        parser.add_argument(
            'data_file',
            help='CSV file name',
        )
        parser.add_argument(
            '--noinput',
            help='Tells Django to NOT prompt the user for input of any kind',
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--skipid',
            action='store_true',
            default=False,
            help="Remove ID value from rows",
        )
        parser.add_argument(
            '-d', '--delimiter',
            dest='delimiter',
            default=',',
            help="Delimiter for csv file",
        )
        parser.add_argument(
            '-e', '--encoding',
            dest='encoding',
            default='utf-8',
            help="Output encoding",
        )

    def handle(self, *args, **options):
        csv.register_dialect(
            "RalphImporter",
            delimiter=str(options['delimiter'])
        )
        settings.REMOVE_ID_FROM_IMPORT = options.get('skipid')

        with open(options.get('data_file')) as csv_file:
            reader_kwargs = {}
            if six.PY2:
                reader_kwargs['encoding'] = options['encoding']
            reader = csv_reader(
                csv_file,
                dialect='RalphImporter',
                **reader_kwargs
            )
            csv_data = list(reader)
            headers, csv_body = csv_data[0], csv_data[1:]
            model_resource = get_resource(options.get('model_name'))
            dataset = tablib.Dataset(*csv_body, headers=headers)
            result = model_resource.import_data(dataset, dry_run=True)
            if result.has_errors():
                for idx, row in enumerate(result.rows):
                    for error in row.errors:
                        error_msg = '\n'.join([
                            'line_number: {}'.format(idx + 1),
                            'error message: {}'.format(error.error),
                            'row data: {}'.format(zip(headers, dataset[idx])),
                            '',
                        ])
                        self.stdout.write(error_msg)
            else:
                if options.get('noinput'):
                    result = model_resource.import_data(dataset, dry_run=False)
                else:
                    for idx, row in enumerate(result.rows):
                        if not row.new_record:
                            info_msg = 'Update: {} {}'.format(
                                idx + 1,
                                row.diff
                            )
                            self.stdout.write(info_msg)
                    answer = input("type 'yes' to save data" + os.linesep)
                    if answer == 'yes':
                        result = model_resource.import_data(
                            dataset,
                            dry_run=False
                        )
                    self.stdout.write("Done")
