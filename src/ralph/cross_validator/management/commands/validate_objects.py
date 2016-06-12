# -*- coding: utf-8 -*-
import logging
from itertools import chain

from django.core.management.base import BaseCommand

from ralph.cross_validator.mappers import mappers
from ralph.cross_validator.validator import check_objects

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def handle(self, *args, **options):
        check_objects(
            chain(
                *[model.objects.all() for model in mappers.keys()]
            )
        )
