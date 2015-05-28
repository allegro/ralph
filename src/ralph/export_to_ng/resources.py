# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.discovery import models_device
from ralph_assets import models_assets

from import_export import fields
from import_export import resources
from import_export import widgets

class DataCenterAssetResource(resources.ModelResource):
    service_env = fields.Field()
    def dehydrate_service_env(self, asset):
        return "{}|{}".format(asset.service.name, asset.device_environment.name)

    class Meta:
        ng_field2ralph_field = {
            ## to be skipped
            #    'id': '',
            #    'asset_ptr': '',
            #    'baseobject_ptr': '',
            ## to be dehydrated
            'service_env': '',
            #    'configuration_path': '',
            # complicated:
            #    'parent': '',
            'barcode': '',
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
        return models_assets.Asset.objects.filter(type=models_assets.AssetType.data_center)[:1]

    def get_export_headers(self):
        #TODO:: make it generic
        from django.utils.encoding import force_text
        ralph_field2ng_field = {
            v or k: k for k, v in DataCenterAssetResource.Meta.ng_field2ralph_field.items()
        }
        headers = [
            ralph_field2ng_field[force_text(field.column_name)]
            for field in self.get_fields()
        ]
        return headers
