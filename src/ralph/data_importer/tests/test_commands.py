# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from django.core import management
from django.test import TestCase

from ralph.assets.models.assets import (
    AssetModel,
    Environment,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.choices import ObjectModelType
from ralph.back_office.models import (
    BackOfficeAsset,
    Warehouse
)
from ralph.data_importer.management.commands import importer
from ralph.data_importer.resources import AssetModelResource


class DataImporterTestCase(TestCase):

    """TestCase data importer command."""

    def setUp(self):
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        asset_model = AssetModel()
        asset_model.name = "asset_model_1"
        asset_model.type = ObjectModelType.back_office
        asset_model.save()

        warehouse = Warehouse()
        warehouse.name = "warehouse_1"
        warehouse.save()

        environment = Environment()
        environment.name = "environment_1"
        environment.save()

        service = Service()
        service.name = "service_1"
        service.save()

        service_environment = ServiceEnvironment()
        service_environment.environment = environment
        service_environment.service = service
        service_environment.save()

    def test_get_resource(self):
        """Test get resources method."""
        asset_model_resource = importer.get_resource('AssetModel')
        self.assertIsInstance(asset_model_resource, AssetModelResource)

    def test_importer_command_warehouse(self):
        """Test importer management command with Warehouse model."""
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput'
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Poznań").exists()
        )

    def test_importer_command_back_office_asset(self):
        """Test importer management command with BackOfficeAsset model."""
        back_office_csv = os.path.join(
            self.base_dir,
            'tests/samples/back_office_assets.csv'
        )
        management.call_command(
            'importer',
            'BackOfficeAsset',
            back_office_csv,
            '--noinput'
        )
        self.assertTrue(BackOfficeAsset.objects.filter(
            sn="bo_asset_sn").exists()
        )
        back_office_asset = BackOfficeAsset.objects.get(sn="bo_asset_sn")
        self.assertEqual(
            back_office_asset.warehouse.name,
            "warehouse_1"
        )
        self.assertEqual(
            back_office_asset.model.name,
            "asset_model_1"
        )
        self.assertEqual(
            back_office_asset.service_env.service.name,
            "service_1"
        )

    def test_importer_command_with_tab(self):
        """Test importer management command with Warehouse model and
        tab separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses_tab.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput',
            delimiter='\t',
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Barcelona").exists()
        )

    def test_importer_command_with_semicolon(self):
        """Test importer management command with Warehouse model and
        semicolon separation file
        """
        warehouse_csv = os.path.join(
            self.base_dir,
            'tests/samples/warehouses_semicolon.csv'
        )
        management.call_command(
            'importer',
            'Warehouse',
            warehouse_csv,
            '--noinput',
            delimiter=';',
        )
        self.assertTrue(Warehouse.objects.filter(
            name="Berlin").exists()
        )
