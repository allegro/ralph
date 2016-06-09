# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from ralph.data_center.models import DataCenterAsset
from ralph.cross_validator.validator import check_object, check_objects

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def __init__(self):
        super().__init__()

    def handle(self, *args, **options):
        check_objects(DataCenterAsset.objects.all())
        # check_objects(DataCenterAsset.objects.filter(id=14227))
        # asset = DataCenterAsset.objects.get(id=14185)
        # print(list(check_object(asset)))
