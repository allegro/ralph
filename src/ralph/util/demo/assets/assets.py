# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime

from ralph.util.demo import DemoData, register
from ralph_assets.models_assets import ModelVisualizationLayout
from ralph_assets.models_dc_assets import Orientation
from ralph_assets.tests.utils.assets import (
    AssetModelFactory, DCAssetFactory, AssetManufacturerFactory
)
from ralph_assets.models_assets import AssetCategory, Service, Warehouse


SAMPLES = {
    'manufacturers': ['HP', 'IBM', 'DELL', 'F5'],
    'models': {
        'rack-server': ['PowerEdge Rxxx'],
        'blade-chassis': ['Super Chassis'],
        'blade-servers': ['DL360', 'DL380p', 'DL380', 'ML10', 'ML10 v21'],
        'pdu': ['Remote Monitored Power Distribution Unit'],
        'load_balancer': ['F5'],
    }
}


@register
class DemoAssetManufacturer(DemoData):
    name = 'assets_manufacturers'
    title = 'Asset manufacturers'

    def generate_data(self, data):
        return {
            name.lower(): AssetManufacturerFactory(name=name)
            for name in SAMPLES['manufacturers']
        }


@register
class DemoAssetCategory(DemoData):
    name = 'assets_categories'
    title = 'Asset categories'

    def generate_data(self, data):
        # loaded from fixtures
        return {
            'rack_server': AssetCategory.objects.get(
                slug='2-2-2-data-center-device-server-rack',
            ),
            'blade_chassis': AssetCategory.objects.get(
                slug='2-2-2-data-center-device-chassis-blade',
            ),
            'blade_server': AssetCategory.objects.get(
                slug='2-2-2-data-center-device-server-blade',
            ),
            'pdu': AssetCategory.objects.get(
                slug='2-2-2-data-center-device-pdu',
            ),
            'load_balancer': AssetCategory.objects.get(
                slug='2-2-2-data-center-device-load-balancer',
            )
        }


@register
class DemoAssetModel(DemoData):
    name = 'assets_models'
    title = 'Asset models'
    required = ['assets_categories', 'assets_manufacturers']

    def generate_data(self, data):
        return {
            'rack_server': AssetModelFactory(
                name=SAMPLES['models']['rack-server'][0],
                manufacturer=data['assets_manufacturers']['hp'],
                category=data['assets_categories']['rack_server'],
                power_consumption=500,
            ),
            'blade_chassis': AssetModelFactory(
                name=SAMPLES['models']['blade-chassis'][0],
                manufacturer=data['assets_manufacturers']['hp'],
                category=data['assets_categories']['blade_chassis'],
                height_of_device=10,
                visualization_layout_front=ModelVisualizationLayout.layout_2x8,
                power_consumption=10,
            ),
            'blade_chassis_ab': AssetModelFactory(
                name=SAMPLES['models']['blade-chassis'][0],
                manufacturer=data['assets_manufacturers']['hp'],
                category=data['assets_categories']['blade_chassis'],
                height_of_device=10,
                visualization_layout_front=ModelVisualizationLayout.layout_2x8AB,  # noqa
                power_consumption=150,
            ),
            'blade_server': AssetModelFactory(
                name=SAMPLES['models']['blade-servers'][0],
                manufacturer=data['assets_manufacturers']['hp'],
                category=data['assets_categories']['blade_server'],
                power_consumption=380,
            ),
            'pdu_model': AssetModelFactory(
                name=SAMPLES['models']['pdu'][0],
                manufacturer=data['assets_manufacturers']['hp'],
                category=data['assets_categories']['pdu'],
            ),
            'load_balancer': AssetModelFactory(
                name=SAMPLES['models']['load_balancer'][0],
                manufacturer=data['assets_manufacturers']['f5'],
                category=data['assets_categories']['load_balancer'],
            )
        }


@register
class DemoDCVisualization(DemoData):
    name = 'assets_dc_assets'
    title = 'DC assets (with visualization)'
    required = [
        'assets_models', 'devices', 'dc', 'racks', 'server_rooms',
        'services', 'envs'
    ]

    def generate_data(self, data):
        blade_location = 3
        service_name = Service.objects.create(name='Office infrastructure')
        warehouse = Warehouse.objects.create(name='Warsaw')
        last_month = datetime.date.today() - datetime.timedelta(days=30)
        return {
            'rack_server': DCAssetFactory(
                model=data['assets_models']['rack_server'],
                device_info__ralph_device_id=data['devices']['device_1'].id,
                device_info__data_center=data['dc']['a'],
                device_info__orientation=Orientation.front,
                device_info__position=1,
                device_info__rack=data['racks']['a'],
                device_info__server_room=data['server_rooms']['a'],
                device_info__slot_no='',
                service=data['services']['backup_systems'],
                device_environment=data['envs']['prod'],
                service_name=service_name,
                warehouse=warehouse,
            ),
            'rack_server': DCAssetFactory(
                model=data['assets_models']['rack_server'],
                device_info__ralph_device_id=data['devices']['device_2'].id,
                device_info__data_center=data['dc']['a'],
                device_info__orientation=Orientation.front,
                device_info__position=2,
                device_info__rack=data['racks']['a'],
                device_info__server_room=data['server_rooms']['a'],
                device_info__slot_no='',
                service=data['services']['databases'],
                device_environment=data['envs']['prod'],
                service_name=service_name,
                warehouse=warehouse,
                invoice_date=last_month,
            ),
            'blade_chassis': DCAssetFactory(
                model=data['assets_models']['blade_chassis'],
                device_info__data_center=data['dc']['a'],
                device_info__position=blade_location,
                device_info__rack=data['racks']['a'],
                device_info__server_room=data['server_rooms']['a'],
                device_info__slot_no='',
                service=data['services']['backup_systems'],
                device_environment=data['envs']['prod'],
                service_name=service_name,
                warehouse=warehouse,
                invoice_date=last_month + datetime.timedelta(days=5),
            ),
            'blade_servers': [
                DCAssetFactory(
                    model=data['assets_models']['blade_chassis'],
                    device_info__data_center=data['dc']['a'],
                    device_info__position=blade_location,
                    device_info__rack=data['racks']['a'],
                    device_info__server_room=data['server_rooms']['a'],
                    device_info__slot_no=slot_no,
                    service=data['services']['backup_systems'],
                    device_environment=data['envs']['prod'],
                    service_name=service_name,
                    warehouse=warehouse,
                    invoice_date=last_month + datetime.timedelta(days=7),
                ) for slot_no in xrange(1, 17)
            ],
            'load_balancer': DCAssetFactory(
                model=data['assets_models']['rack_server'],
                device_info__ralph_device_id=data['devices']['device_3'].id,
                device_info__data_center=data['dc']['a'],
                device_info__orientation=Orientation.front,
                device_info__position=20,
                device_info__rack=data['racks']['a'],
                device_info__server_room=data['server_rooms']['a'],
                device_info__slot_no='',
                service=data['services']['load_balancing'],
                device_environment=data['envs']['prod'],
                service_name=service_name,
                warehouse=warehouse,
            )
        }
