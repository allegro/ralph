from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from import_export import fields
from import_export import resources
from import_export import widgets

from ralph.assets.models import assets
from ralph.data_center.models import physical


class AssetModelResource(resources.ModelResource):
    category = fields.Field(
        column_name='asset category',
        attribute='category',
        widget=widgets.ForeignKeyWidget(assets.Category, 'name'),
    )
    class Meta:
        model = assets.AssetModel
        fields = ('id', 'name', 'type', 'category')

class DataCenterAssetResource(resources.ModelResource):
    model = fields.Field(
        column_name='asset model',
        attribute='model',
        widget=widgets.ForeignKeyWidget(assets.AssetModel, 'name')
    )
    connections = fields.Field(
        column_name='connections',
        attribute='connections',
        widget=widgets.ManyToManyWidget(physical.DataCenterAsset, field='sn')
    )
    class Meta:
        model = physical.DataCenterAsset
        #exclude = ('connections',)
        #fields = ('id', 'model', 'service_env')

#exclude:
    #asset_ptr
    #baseobject_ptr
    #created
    #modified

#fk:
    #parent
    #service_env
    #model

#TODO:
    #id
    #remarks
    #hostname
    #niw
    #invoice_no
    #required_support
    #order_no
    #purchase_order
    #invoice_date
    #sn
    #barcode
    #price
    #provider
    #source
    #status
    #request_date
    #delivery_date
    #production_use_date
    #provider_order_date
    #deprecation_rate
    #force_deprecation
    #deprecation_end_date
    #production_year
    #task_url
    #loan_end_date
    #rack
    #slots
    #slot_no
    #configuration_path
    #position
    #orientation
    #connections


