from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Count
from import_export import fields, resources, widgets

from ralph.accounts.models import Region
from ralph.assets.models import assets, base, configuration
from ralph.back_office.models import (
    BackOfficeAsset,
    OfficeInfrastructure,
    Warehouse
)
from ralph.data_center.models import physical
from ralph.data_importer.fields import ThroughField
from ralph.data_importer.mixins import (
    ImportForeignKeyMeta,
    ImportForeignKeyMixin
)
from ralph.data_importer.widgets import (
    AssetServiceEnvWidget,
    BaseObjectManyToManyWidget,
    BaseObjectWidget,
    ImportedForeignKeyWidget,
    ManyToManyThroughWidget,
    NullStringWidget,
    UserManyToManyWidget,
    UserWidget
)
from ralph.domains.models.domains import Domain, DomainContract
from ralph.licences.models import (
    BaseObjectLicence,
    Licence,
    LicenceType,
    LicenceUser,
    Software
)
from ralph.networks.models import networks
from ralph.operations.models import Operation, OperationType
from ralph.supports.models import BaseObjectsSupport, Support, SupportType

RalphResourceMeta = type(
    'RalphResourceMeta',
    (
        ImportForeignKeyMeta,
        resources.ModelDeclarativeMetaclass,
        resources.Resource
    ),
    {}
)


class RalphModelResource(
    ImportForeignKeyMixin,
    resources.ModelResource,
    metaclass=RalphResourceMeta
):
    pass


class AssetModelResource(RalphModelResource):
    manufacturer = fields.Field(
        column_name='manufacturer',
        attribute='manufacturer',
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ImportedForeignKeyWidget(assets.Category),
    )
    assets_count = fields.Field(
        readonly=True,
        column_name='assets_count',
        attribute='assets_count',
    )

    class Meta:
        model = assets.AssetModel

    def get_queryset(self):
        return assets.AssetModel.objects.annotate(assets_count=Count('assets'))

    def dehydrate_assets_count(self, model):
        # check if model has `assets_count` attribute first (it's only included
        # when using annotated queryset above)
        return (
            model.assets_count
            if hasattr(model, 'assets_count')
            else model.assets.count()
        )


class CategoryResource(RalphModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(assets.Category),
    )

    class Meta:
        model = assets.Category


class BackOfficeAssetResource(RalphModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(assets.Asset),
    )
    service_env = fields.Field(
        column_name='service_env',
        attribute='service_env',
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=UserWidget(get_user_model()),
    )
    owner = fields.Field(
        column_name='owner',
        attribute='owner',
        widget=UserWidget(get_user_model()),
    )
    warehouse = fields.Field(
        column_name='warehouse',
        attribute='warehouse',
        widget=ImportedForeignKeyWidget(Warehouse),
    )
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ImportedForeignKeyWidget(Region),
    )
    property_of = fields.Field(
        column_name='property_of',
        attribute='property_of',
        widget=ImportedForeignKeyWidget(assets.AssetHolder),
    )
    budget_info = fields.Field(
        column_name='budget_info',
        attribute='budget_info',
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )

    class Meta:
        model = BackOfficeAsset
        prefetch_related = (
            'tags',
        )
        exclude = ('content_type', 'asset_ptr', 'baseobject_ptr',)

    def dehydrate_price(self, bo_asset):
        return str(bo_asset.price)

    def dehydrate_depreciation_rate(self, bo_asset):
        return str(bo_asset.depreciation_rate)


class ServerRoomResource(RalphModelResource):
    data_center = fields.Field(
        column_name='data_center',
        attribute='data_center',
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )

    class Meta:
        model = physical.ServerRoom


class RackResource(RalphModelResource):
    server_room = fields.Field(
        column_name='server_room',
        attribute='server_room',
        widget=ImportedForeignKeyWidget(physical.ServerRoom),
    )

    class Meta:
        model = physical.Rack


class DiscoveryDataCenterResource(RalphModelResource):
    """
    Imports datacenters from Discovery.DataCenter (Ralph2).

    In Ralph2 data centers was in two tables:
        - Assets data centers
        - Discovery data centers
    Ralph3 stores all data centers in one table (physical.DataCenter), so this
    resource allows to import discovery data centers from Ralph2.
    """
    class Meta:
        model = physical.DataCenter


class NetworkResource(RalphModelResource):
    data_center = fields.Field(
        column_name='data_center',
        attribute='data_center',
        widget=ImportedForeignKeyWidget(physical.DataCenter),
    )
    network_environment = fields.Field(
        column_name='network_environment',
        attribute='network_environment',
        widget=ImportedForeignKeyWidget(networks.NetworkEnvironment),
    )
    kind = fields.Field(
        column_name='kind',
        attribute='kind',
        widget=ImportedForeignKeyWidget(networks.NetworkKind),
    )
    terminators = fields.Field(
        column_name='terminators',
        attribute='terminators',
        widget=BaseObjectManyToManyWidget(model=assets.BaseObject),
    )

    class Meta:
        model = networks.Network
        exclude = ('gateway_as_int', 'min_ip', 'max_ip')


class IPAddressResource(RalphModelResource):

    base_object = fields.Field(
        column_name='asset',
        attribute='base_object',
        widget=BaseObjectWidget(assets.BaseObject),
    )

    network = fields.Field(
        column_name='network',
        attribute='network',
        widget=ImportedForeignKeyWidget(networks.Network),
    )

    class Meta:
        model = networks.IPAddress

    def skip_row(self, instance, original):
        if settings.MAP_IMPORTED_ID_TO_NEW_ID:
            try:
                networks.IPAddress.objects.get(address=instance.address)
            except networks.IPAddress.DoesNotExist:
                pass
            else:
                return True
        return False


class DataCenterAssetResource(RalphModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    service_env = fields.Field(
        column_name='service_env',
        attribute='service_env',
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment, 'name'),
    )
    model = fields.Field(
        column_name='model',
        attribute='model',
        widget=ImportedForeignKeyWidget(assets.AssetModel),
    )
    rack = fields.Field(
        column_name='rack',
        attribute='rack',
        widget=ImportedForeignKeyWidget(physical.Rack),
    )
    budget_info = fields.Field(
        column_name='budget_info',
        attribute='budget_info',
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )
    management_ip = fields.Field(
        column_name='management_ip',
        attribute='management_ip',
        widget=NullStringWidget(),
    )

    class Meta:
        model = physical.DataCenterAsset
        select_related = (
            'service_env__service', 'service_env__environment',
            'rack__server_room__data_center',
        )
        prefetch_related = (
            'tags',
        )
        exclude = ('content_type', 'asset_ptr', 'baseobject_ptr', 'connections')

    def dehydrate_price(self, dc_asset):
        return str(dc_asset.price)

    def dehydrate_depreciation_rate(self, dc_asset):
        return str(dc_asset.depreciation_rate)


class ConnectionResource(RalphModelResource):
    outbound = fields.Field(
        column_name='outbound',
        attribute='outbound',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )
    inbound = fields.Field(
        column_name='outbound',
        attribute='outbound',
        widget=ImportedForeignKeyWidget(physical.DataCenterAsset),
    )

    class Meta:
        model = physical.Connection


class LicenceResource(RalphModelResource):
    manufacturer = fields.Field(
        column_name='manufacturer',
        attribute='manufacturer',
        widget=ImportedForeignKeyWidget(assets.Manufacturer),
    )
    licence_type = fields.Field(
        column_name='licence_type',
        attribute='licence_type',
        widget=ImportedForeignKeyWidget(LicenceType),
    )
    software = fields.Field(
        column_name='software',
        attribute='software',
        widget=ImportedForeignKeyWidget(Software),
    )
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ImportedForeignKeyWidget(Region),
    )
    office_infrastructure = fields.Field(
        column_name='office_infrastructure',
        attribute='office_infrastructure',
        widget=ImportedForeignKeyWidget(OfficeInfrastructure),
    )
    users = ThroughField(
        column_name='users',
        attribute='users',
        widget=UserManyToManyWidget(model=LicenceUser),
        through_model=LicenceUser,
        through_from_field_name='licence',
        through_to_field_name='user'
    )
    base_objects = ThroughField(
        column_name='base_objects',
        attribute='baseobjectlicence_set',
        widget=ManyToManyThroughWidget(
            model=BaseObjectLicence,
            related_model=base.BaseObject,
            through_field='base_object'
        ),
        through_model=BaseObjectLicence,
        through_from_field_name='licence',
        through_to_field_name='base_object'
    )

    class Meta:
        model = Licence
        prefetch_related = ('tags',)
        exclude = ('content_type', 'baseobject_ptr', )

    def get_queryset(self):
        return Licence.objects_used_free_with_related.all()

    def dehydrate_price(self, licence):
        return str(licence.price)


class SupportTypeResource(RalphModelResource):

    class Meta:
        model = SupportType


class SupportResource(RalphModelResource):
    support_type = fields.Field(
        column_name='support_type',
        attribute='support_type',
        widget=ImportedForeignKeyWidget(SupportType),
    )
    base_objects = ThroughField(
        column_name='base_objects',
        attribute='baseobjectssupport_set',
        widget=ManyToManyThroughWidget(
            model=BaseObjectsSupport,
            related_model=base.BaseObject,
            through_field='baseobject'
        ),
        through_model=BaseObjectsSupport,
        through_from_field_name='support',
        through_to_field_name='baseobject'
    )
    region = fields.Field(
        column_name='region',
        attribute='region',
        widget=ImportedForeignKeyWidget(Region),
    )
    budget_info = fields.Field(
        column_name='budget_info',
        attribute='budget_info',
        widget=ImportedForeignKeyWidget(assets.BudgetInfo),
    )
    property_of = fields.Field(
        column_name='property_of',
        attribute='property_of',
        widget=ImportedForeignKeyWidget(assets.AssetHolder),
    )
    assigned_objects_count = fields.Field(
        readonly=True,
        column_name='assigned_objects_count',
        attribute='assigned_objects_count',
    )

    class Meta:
        model = Support
        exclude = ('content_type', 'baseobject_ptr',)
        prefetch_related = ('tags',)

    def get_queryset(self):
        return Support.objects_with_related.all()

    def dehydrate_assigned_objects_count(self, support):
        return support.assigned_objects_count

    def dehydrate_price(self, support):
        return str(support.price)


class ProfitCenterResource(RalphModelResource):
    business_segment = fields.Field(
        column_name='business_segment',
        attribute='business_segment',
        widget=ImportedForeignKeyWidget(assets.BusinessSegment),
    )

    class Meta:
        model = assets.ProfitCenter


class ServiceResource(RalphModelResource):
    profit_center = fields.Field(
        column_name='profit_center',
        attribute='profit_center',
        widget=ImportedForeignKeyWidget(assets.ProfitCenter),
    )
    business_owners = fields.Field(
        column_name='business_owners',
        attribute='business_owners',
        widget=UserManyToManyWidget(get_user_model()),
    )
    technical_owners = fields.Field(
        column_name='technical_owners',
        attribute='technical_owners',
        widget=UserManyToManyWidget(get_user_model()),
    )
    environments = ThroughField(
        column_name='environments',
        attribute='environments',
        widget=widgets.ManyToManyWidget(model=assets.Environment),
        through_model=assets.ServiceEnvironment,
        through_from_field_name='service',
        through_to_field_name='environment'
    )

    class Meta:
        model = assets.Service


class ServiceEnvironmentResource(RalphModelResource):
    service = fields.Field(
        column_name='service',
        attribute='service',
        widget=ImportedForeignKeyWidget(assets.Service),
    )
    environment = fields.Field(
        column_name='environment',
        attribute='environment',
        widget=ImportedForeignKeyWidget(assets.Environment),
    )

    class Meta:
        model = assets.ServiceEnvironment


class BaseObjectLicenceResource(RalphModelResource):
    licence = fields.Field(
        column_name='licence',
        attribute='licence',
        widget=ImportedForeignKeyWidget(Licence),
    )
    base_object = fields.Field(
        column_name='base_object',
        attribute='base_object',
        widget=BaseObjectWidget(base.BaseObject),
    )

    class Meta:
        model = BaseObjectLicence


class LicenceUserResource(RalphModelResource):
    licence = fields.Field(
        column_name='licence',
        attribute='licence',
        widget=ImportedForeignKeyWidget(Licence),
    )
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=UserWidget(get_user_model()),
    )

    class Meta:
        model = LicenceUser


class BaseObjectsSupportResource(RalphModelResource):
    support = fields.Field(
        column_name='support',
        attribute='support',
        widget=ImportedForeignKeyWidget(Support),
    )
    baseobject = fields.Field(
        column_name='baseobject',
        attribute='baseobject',
        widget=BaseObjectWidget(base.BaseObject),
    )

    class Meta:
        model = BaseObjectsSupport


class RackAccessoryResource(RalphModelResource):
    accessory = fields.Field(
        column_name='accessory',
        attribute='accessory',
        widget=ImportedForeignKeyWidget(physical.Accessory),
    )
    rack = fields.Field(
        column_name='rack',
        attribute='rack',
        widget=ImportedForeignKeyWidget(physical.Rack),
    )

    class Meta:
        model = physical.RackAccessory


class RegionResource(RalphModelResource):
    users = fields.Field(
        column_name='users',
        attribute='users',
        widget=UserManyToManyWidget(get_user_model()),
    )

    class Meta:
        model = Region


class AssetHolderResource(RalphModelResource):

    class Meta:
        model = assets.AssetHolder


class OfficeInfrastructureResource(RalphModelResource):

    class Meta:
        model = OfficeInfrastructure


class BudgetInfoResource(RalphModelResource):

    class Meta:
        model = assets.BudgetInfo


class DomainContractResource(RalphModelResource):
    domain = fields.Field(
        column_name='domain',
        attribute='domain',
        widget=widgets.ForeignKeyWidget(Domain, 'name'),
    )

    class Meta:
        model = DomainContract


class DomainResource(RalphModelResource):
    business_segment = fields.Field(
        column_name='business_segment',
        attribute='business_segment',
        widget=widgets.ForeignKeyWidget(
            assets.BusinessSegment, 'name',
        ),
    )
    business_owner = fields.Field(
        column_name='business_owner',
        attribute='business_owner',
        widget=UserWidget(get_user_model()),
    )
    technical_owner = fields.Field(
        column_name='technical_owner',
        attribute='technical_owner',
        widget=UserWidget(get_user_model()),
    )
    domain_holder = fields.Field(
        column_name='domain_holder',
        attribute='domain_holder',
        widget=widgets.ForeignKeyWidget(assets.AssetHolder),
    )
    service_env = fields.Field(
        column_name='service_env',
        attribute='service_env',
        widget=AssetServiceEnvWidget(assets.ServiceEnvironment),
    )

    class Meta:
        model = Domain
        exclude = ('baseobject_ptr',)


class OperationTypeResource(RalphModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(OperationType),
    )

    class Meta:
        model = OperationType


class OperationResource(RalphModelResource):
    type = fields.Field(
        column_name='type',
        attribute='type',
        widget=ImportedForeignKeyWidget(OperationType),
    )
    base_objects = fields.Field(
        column_name='base_objects',
        attribute='base_objects',
        widget=widgets.ManyToManyWidget(base.BaseObject),
        default=[],
    )
    asignee = fields.Field(
        column_name='asignee',
        attribute='asignee',
        widget=UserWidget(get_user_model()),
    )

    class Meta:
        model = Operation


class ConfigurationModuleResource(RalphModelResource):
    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget=ImportedForeignKeyWidget(configuration.ConfigurationModule),
    )

    class Meta:
        model = configuration.ConfigurationModule


class ConfigurationClassResource(RalphModelResource):
    module = fields.Field(
        column_name='module',
        attribute='module',
        widget=ImportedForeignKeyWidget(configuration.ConfigurationModule),
    )

    class Meta:
        model = configuration.ConfigurationClass
