# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

import tablib
from django.core.management.base import BaseCommand
from django.db.models.loading import get_models
from import_export import resources

from ralph.lib import unicode_csv

APP_MODELS = {model._meta.model_name: model for model in get_models()}

try:
    # python 2.x and 3.x comability
    input = raw_input
except NameError:
    pass


def get_resource(model_name):
    model_class = APP_MODELS[model_name.lower()]
    return resources.modelresource_factory(model=model_class)()


class Command(BaseCommand):
    help = 'Imports data for specified model from specified file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model_name', default=False, help='TODO::',
        )
        parser.add_argument(
            '--data_file', default=False, help='TODO::',
        )

    def handle(self, *args, **options):
        with open(options.get('data_file')) as csv_file:
            reader = unicode_csv.UnicodeReader(csv_file)
            csv_data = list(reader)
            headers, csv_body = csv_data[0], csv_data[1:]
            model_resource = get_resource(options.get('model_name'))
            dataset = tablib.Dataset(*csv_body, headers=headers)
            result = model_resource.import_data(dataset, dry_run=True)
            if result.has_errors():
                for idx, row in enumerate(result.rows):
                    for error in row.errors:
                        error_msg = '\n'.join([
                            'line_number: {}'.format(idx+1),
                            'error message: {}'.format(error.error),
                            'row data: {}'.format(zip(headers, dataset[idx])),
                            '',
                        ])
                        self.stdout.write(error_msg)
            else:
                for idx, row in enumerate(result.rows):
                    self.stdout.write("Found rows to update:")
                    if not row.new_record:
                        info_msg = '{} {}'.format(idx + 1, row.diff)
                        self.stdout.write(info_msg)
                answer = input("type 'yes' to save data" + os.linesep)
                if answer == 'yes':
                    # TODO: optimize it (this is the second call of import_data)
                    result = model_resource.import_data(dataset, dry_run=False)
