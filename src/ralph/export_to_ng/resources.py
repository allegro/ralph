# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.encoding import force_text
from import_export import fields
from import_export import resources
from import_export import widgets
from ralph.discovery import models_device

from ralph_assets import models_assets


class RalphResourceMixin(resources.ModelResource):
    def get_export_headers(self):
        ralph_field2ng_field = {
            v or k: k for k, v in self.__class__.Meta.ng_field2ralph_field.items()
        }
        headers = [
            ralph_field2ng_field[force_text(field.column_name)]
            for field in self.get_fields()
        ]
        return headers


class DataCenterAssetResource(RalphResourceMixin, resources.ModelResource):
    service_env = fields.Field()

    def dehydrate_id(self, asset):
        return ""

    def dehydrate_service_env(self, asset):
        return "{}|{}".format(asset.service.name, asset.device_environment.name)

    class Meta:
        ng_field2ralph_field = {
            ## to be skipped
                'id': '',
            #    'asset_ptr': '',
            #    'baseobject_ptr': '',
            ## to be dehydrated
            'service_env': '',
            #TODO::
            #    'configuration_path': '',
            # complicated:
            #TODO::
            #    'parent': '',
            'barcode': '',
            #TODO:: m2m
            'connections': '',
            'created': '',
            'delivery_date': '',
            'deprecation_end_date': '',
            'deprecation_rate': '',
            'force_deprecation': '',
            'invoice_date': '',
            'invoice_no': '',
            'loan_end_date': '',
            'model': 'model__name',
            'modified': '',
            'niw': '',
            'order_no': '',
            'orientation': 'device_info__orientation',
            'position': '',
            'price': '',
            'production_use_date': '',
            'production_year': '',
            'provider': '',
            'provider_order_date': '',
            'purchase_order': '',
            'rack': 'device_info__rack__name',
            'remarks': '',
            'request_date': '',
            'required_support': '',
            'slot_no': 'device_info__slot_no',
            'slots': '',
            'sn': '',
            'source': '',
            'status': '',
            'task_url': '',
            'hostname': 'device_info__ralph_device__name',
        }
        fields = [v or k for k, v in ng_field2ralph_field.items()]
        model = models_assets.Asset

    def get_queryset(self):
        #return self._meta.model.objects.all()
        return self.Meta.model.objects.filter(
            type=models_assets.AssetType.data_center
        #TODO:: remove it
        )[:1]


class AssetModelResource(RalphResourceMixin, resources.ModelResource):
    class Meta:
        ng_field2ralph_field = {
            'category': 'category__name',
            'cores_count': '',
            'height_of_device': '',
            'manufacturer': 'manufacturer__name',
            'power_consumption': '',
            'visualization_layout_back': '',
            'visualization_layout_front': '',
            ## verify, these missing in old ralph
            #'created': '',
            #'id': '',
            #'modified': '',
            #'name': '',
            #'type': '',
        }
        fields = [v or k for k, v in ng_field2ralph_field.items()]
        model = models_assets.AssetModel

    def get_queryset(self):
        return self.Meta.model.objects.filter()[:1]
