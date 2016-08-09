# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from ralph.data_importer.models import ImportedObjects
from ralph.cross_validator.ralph2.device import Asset

logger = logging.getLogger(__name__)

ci_prefix_mappings = {
    'DataCenterAsset': 'dd',
    'VirtualServer': 'dd',
    'Network': 'dn',
    'ConfigurationModule': 'bv',
    'ConfigurationClass': 'br',
    'Service': 'sc',
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--model-name',
            help='The model name to which the import data',
            choices=list(ci_prefix_mappings.keys()) + ['all'],
            default='all',
            dest='model',
        )

    def handle(self, *args, **options):
        # NetworkTerminator ??
        if options.get('model') == 'all':
            models = ci_prefix_mappings.keys()
        else:
            models = [options.get('model')]
        for model in models:
            ct = ContentType.objects.get(model=model)
            handler = getattr(
                self, 'handle_{}'.format(model.lower()), None
            )
            prefix = ci_prefix_mappings[model]
            if handler:
                handler(ct, prefix)
            else:
                self.generic_handler(ct, prefix)

    def generic_handler(self, ct, prefix):
        for io in ImportedObjects.objects.filter(content_type=ct):
            io.old_ci_uid = '{}-{}'.format(prefix, io.old_object_pk)
            io.save()

    def handle_datacenterasset(self, ct, prefix):
        mapping = dict(Asset.objects.using('ralph2').filter(
            device_info__ralph_device_id__isnull=False
        ).values_list(
            'pk', 'device_info__ralph_device_id'
        ))
        for io in ImportedObjects.objects.filter(content_type=ct):
            device_id = mapping.get(io.old_object_pk)
            if device_id:
                io.old_ci_uid = '{}-{}'.format(prefix, device_id)
                io.save()

    def handle_service(self, ct, prefix):
        for io in ImportedObjects.objects.filter(content_type=ct):
            try:
                service = io.object
            except ObjectDoesNotExist:
                pass
            else:
                if service:
                    io.old_ci_uid = service.uid
                    io.save()
