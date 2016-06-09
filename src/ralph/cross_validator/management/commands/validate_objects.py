# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from ralph.cross_validator.mappers import mappers
from ralph.cross_validator.models import CrossValidationRun
from ralph.cross_validator.validator import check_objects_of_single_type

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            help='The model name to which the import data',
            choices=list(mappers.keys()) + ['all'],
            default='all',
            dest='model',
        )

    def handle(self, *args, **options):
        run = CrossValidationRun.objects.create()
        if options.get('model') == 'all':
            models = mappers.keys()
        else:
            models = [options.get('model')]
        for model_name in models:
            model_config = mappers[model_name]
            logger.info('Validating {}'.format(model_name))
            valid, invalid = check_objects_of_single_type(model_config, run)
            run.valid_count += valid
            run.invalid_count += invalid
            run.checked_count += (valid + invalid)
        run.save()
