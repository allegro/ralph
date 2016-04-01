# -*- coding: utf-8 -*-
import os
import random
from itertools import cycle

from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ralph.accounts.models import RalphUser
from ralph.accounts.tests.factories import (
    GroupFactory,
    RegionFactory,
    UserFactory
)
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    CategoryFactory,
    DataCenterAssetModelFactory,
    DataCenterCategoryFactory,
    ProfitCenterFactory,
    ServiceEnvironmentFactory
)
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models.choices import DataCenterAssetStatus
from ralph.data_center.models.physical import DataCenterAsset
from ralph.data_center.tests.factories import (
    AccessoryFactory,
    DataCenterAssetFactory,
    RackAccessoryFactory,
    RackFactory,
    ServerRoomFactory
)
from ralph.lib.transitions.models import Action, Transition, TransitionModel
from ralph.licences.models import LicenceUser
from ralph.licences.tests.factories import (
    BaseObjectLicenceFactory,
    DataCenterAssetLicenceFactory,
    LicenceFactory
)
from ralph.reports.models import Report, ReportLanguage, ReportTemplate
from ralph.supports.tests.factories import BaseObjectsSupportFactory


def get_imei(n):
    """Random IMEI generator. This function return random but not unique
    IMEI number. Based on code from http://stackoverflow.com/a/20733310
    """
    def luhn_residue(digits):
        """Luhn algorithm"""
        return sum(sum(divmod(int(d) * (1 + i % 2), 10))
                   for i, d in enumerate(digits[::-1])) % 10

    part = ''.join(str(random.randrange(0, 9)) for _ in range(n - 1))
    res = luhn_residue('{}{}'.format(part, 0))
    return '{}{}'.format(part, -res % 10)


class Command(BaseCommand):

    help = "Generating demo data."
    all_apps = [
        'backoffice', 'datacenter', 'licences', 'supports', 'transitions'
    ]
    object_limit = 30

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--apps',
            choices=self.all_apps + ['all'],
            default='all',
            dest='apps',
            help='One or more apps separated by comma.'
        )
        parser.add_argument(
            '-f', '--flush',
            default=False,
            action='store_true',
            dest='flush',
            help='Flush database before generate.'
        )

    def generate_data_center(self):
        self.stdout.write('Generating Data Center assets')
        data_center_status = DataCenterAssetStatus()
        parent_category = DataCenterCategoryFactory(
            name='DATA CENTER',
            imei_required=False
        )
        for i in range(2):
            server_room = ServerRoomFactory()
            visualization_col = 1
            visualization_row = 1
            for j in range(10):
                rack = RackFactory(
                    server_room=server_room,
                    visualization_row=visualization_row,
                    visualization_col=visualization_col
                )
                visualization_row += 1
                if (
                    visualization_row >
                    server_room.data_center.visualization_rows_num
                ):
                    visualization_row = 1
                    visualization_col += 1

                accessory = AccessoryFactory()
                RackAccessoryFactory(rack=rack, accessory=accessory)
                position = 1
                for status_id, name in data_center_status:
                    for i in range(2):
                        asset_model = DataCenterAssetModelFactory(
                            category=DataCenterCategoryFactory(
                                parent=parent_category
                            )
                        )
                        DataCenterAssetFactory(
                            rack=rack,
                            status=status_id,
                            position=position,
                            slot_no='',
                            service_env=ServiceEnvironmentFactory(),
                            model=asset_model
                        )
                        position += asset_model.height_of_device
                        if position > rack.max_u_height:
                            position = 1

            chassis = DataCenterAssetFactory(
                rack=rack,
                status=DataCenterAssetStatus.used.id,
                position=38,
                slot_no=None,
                service_env=ServiceEnvironmentFactory(),
                model=DataCenterAssetModelFactory(
                    name='Chassis',
                    category=DataCenterCategoryFactory(parent=parent_category),
                    height_of_device=5
                )
            )
            for i in range(5):
                DataCenterAssetFactory(
                    rack=rack,
                    status=DataCenterAssetStatus.used.id,
                    position=None,
                    service_env=ServiceEnvironmentFactory(),
                    slot_no=i,
                    parent=chassis,
                    model=DataCenterAssetModelFactory(
                        name='Blade',
                        has_parent=True,
                        category=DataCenterCategoryFactory(
                            parent=parent_category
                        )
                    )
                )

    def generate_back_office(self):
        self.stdout.write('Generating Back Office assets')
        back_office_status = BackOfficeAssetStatus()
        status_count = len(back_office_status)
        per_page = self.object_limit / status_count
        parent_category = CategoryFactory(
            name='BACK OFFICE',
            imei_required=False
        )
        for i in range(3):
            ProfitCenterFactory()

        for status_id, name in back_office_status:
            for i in range(int(per_page)):
                BackOfficeAssetFactory(
                    status=status_id,
                    user=self.get_user(),
                    owner=self.get_user(),
                    model=BackOfficeAssetModelFactory(
                        category=CategoryFactory(parent=parent_category)
                    )
                )
                BackOfficeAssetFactory(
                    status=status_id,
                    user=self.get_user(),
                    owner=self.get_user(),
                    model=BackOfficeAssetModelFactory(
                        category=CategoryFactory(
                            name='Mobile Phone',
                            imei_required=True,
                            parent=parent_category
                        ),
                        name='Phone'
                    ),
                    imei=get_imei(15)
                )

    def generate_users_and_groups(self):
        self.stdout.write('Generating Users and Groups')

        def add_user_and_group(username, password, group_name, permissions):
            group = GroupFactory(name=group_name)
            for codename in permissions:
                group.permissions.add(
                    Permission.objects.get(codename=codename)
                )

            user = UserFactory(
                username=username,
                is_staff=True
            )
            user.regions.add(RegionFactory())
            user.set_password(password)
            user.groups.add(group)
            user.save()

        dc_permissions = [
            'view_region',
            'view_region_country_field',
            'view_region_id_field',
            'view_region_name_field',
            'add_assetmodel',
            'change_assetmodel',
            'change_assetmodel_category_field',
            'change_assetmodel_cores_count_field',
            'change_assetmodel_has_parent_field',
            'change_assetmodel_height_of_device_field',
            'change_assetmodel_manufacturer_field',
            'change_assetmodel_name_field',
            'change_assetmodel_power_consumption_field',
            'change_assetmodel_type_field',
            'change_assetmodel_visualization_layout_back_field',
            'change_assetmodel_visualization_layout_front_field',
            'delete_assetmodel',
            'view_assetmodel',
            'view_assetmodel_category_field',
            'view_assetmodel_cores_count_field',
            'view_assetmodel_has_parent_field',
            'view_assetmodel_height_of_device_field',
            'view_assetmodel_id_field',
            'view_assetmodel_manufacturer_field',
            'view_assetmodel_name_field',
            'view_assetmodel_power_consumption_field',
            'view_assetmodel_type_field',
            'view_assetmodel_visualization_layout_back_field',
            'view_assetmodel_visualization_layout_front_field',
            'add_environment',
            'change_environment',
            'delete_environment',
            'view_environment',
            'add_service',
            'change_service',
            'delete_service',
            'view_service',
            'add_serviceenvironment',
            'change_serviceenvironment',
            'change_serviceenvironment_content_type_field',
            'change_serviceenvironment_environment_field',
            'change_serviceenvironment_parent_field',
            'change_serviceenvironment_remarks_field',
            'change_serviceenvironment_service_env_field',
            'change_serviceenvironment_service_field',
            'change_serviceenvironment_tags_field',
            'delete_serviceenvironment',
            'view_serviceenvironment',
            'view_serviceenvironment_baseobject_ptr_field',
            'view_serviceenvironment_content_type_field',
            'view_serviceenvironment_environment_field',
            'view_serviceenvironment_id_field',
            'view_serviceenvironment_parent_field',
            'view_serviceenvironment_remarks_field',
            'view_serviceenvironment_service_env_field',
            'view_serviceenvironment_service_field',
            'view_serviceenvironment_tags_field',
            'add_accessory',
            'change_accessory',
            'delete_accessory',
            'view_accessory',
            'add_database',
            'change_database',
            'change_database_content_type_field',
            'change_database_parent_field',
            'change_database_remarks_field',
            'change_database_service_env_field',
            'change_database_tags_field',
            'delete_database',
            'view_database',
            'view_database_baseobject_ptr_field',
            'view_database_content_type_field',
            'view_database_id_field',
            'view_database_parent_field',
            'view_database_remarks_field',
            'view_database_service_env_field',
            'view_database_tags_field',
            'add_datacenter',
            'change_datacenter',
            'delete_datacenter',
            'view_datacenter',
            'add_datacenterasset',
            'can_view_extra_datacenterassetadminattachmentsview',
            'can_view_extra_datacenterassetcomponents',
            'can_view_extra_datacenterassetlicence',
            'can_view_extra_datacenterassetsecurityinfo',
            'can_view_extra_datacenterassetsupport',
            'can_view_extra_networkview',
            'change_datacenterasset',
            'change_datacenterasset_barcode_field',
            'change_datacenterasset_budget_info_field',
            'change_datacenterasset_connections_field',
            'change_datacenterasset_content_type_field',
            'change_datacenterasset_delivery_date_field',
            'change_datacenterasset_depreciation_end_date_field',
            'change_datacenterasset_depreciation_rate_field',
            'change_datacenterasset_force_depreciation_field',
            'change_datacenterasset_hostname_field',
            'change_datacenterasset_invoice_date_field',
            'change_datacenterasset_invoice_no_field',
            'change_datacenterasset_management_hostname_field',
            'change_datacenterasset_management_ip_field',
            'change_datacenterasset_model_field',
            'change_datacenterasset_niw_field',
            'change_datacenterasset_order_no_field',
            'change_datacenterasset_orientation_field',
            'change_datacenterasset_parent_field',
            'change_datacenterasset_position_field',
            'change_datacenterasset_price_field',
            'change_datacenterasset_production_use_date_field',
            'change_datacenterasset_production_year_field',
            'change_datacenterasset_property_of_field',
            'change_datacenterasset_provider_field',
            'change_datacenterasset_rack_field',
            'change_datacenterasset_remarks_field',
            'change_datacenterasset_required_support_field',
            'change_datacenterasset_service_env_field',
            'change_datacenterasset_slot_no_field',
            'change_datacenterasset_sn_field',
            'change_datacenterasset_source_field',
            'change_datacenterasset_status_field',
            'change_datacenterasset_tags_field',
            'change_datacenterasset_task_url_field',
            'delete_datacenterasset',
            'view_datacenterasset',
            'view_datacenterasset_asset_ptr_field',
            'view_datacenterasset_barcode_field',
            'view_datacenterasset_baseobject_ptr_field',
            'view_datacenterasset_budget_info_field',
            'view_datacenterasset_connections_field',
            'view_datacenterasset_content_type_field',
            'view_datacenterasset_delivery_date_field',
            'view_datacenterasset_depreciation_end_date_field',
            'view_datacenterasset_depreciation_rate_field',
            'view_datacenterasset_force_depreciation_field',
            'view_datacenterasset_hostname_field',
            'view_datacenterasset_id_field',
            'view_datacenterasset_invoice_date_field',
            'view_datacenterasset_invoice_no_field',
            'view_datacenterasset_management_hostname_field',
            'view_datacenterasset_management_ip_field',
            'view_datacenterasset_model_field',
            'view_datacenterasset_niw_field',
            'view_datacenterasset_order_no_field',
            'view_datacenterasset_orientation_field',
            'view_datacenterasset_parent_field',
            'view_datacenterasset_position_field',
            'view_datacenterasset_price_field',
            'view_datacenterasset_production_use_date_field',
            'view_datacenterasset_production_year_field',
            'view_datacenterasset_property_of_field',
            'view_datacenterasset_provider_field',
            'view_datacenterasset_rack_field',
            'view_datacenterasset_remarks_field',
            'view_datacenterasset_required_support_field',
            'view_datacenterasset_service_env_field',
            'view_datacenterasset_slot_no_field',
            'view_datacenterasset_sn_field',
            'view_datacenterasset_source_field',
            'view_datacenterasset_status_field',
            'view_datacenterasset_tags_field',
            'view_datacenterasset_task_url_field',
            'add_ipaddress',
            'change_ipaddress',
            'delete_ipaddress',
            'view_ipaddress',
            'add_rack',
            'change_rack',
            'delete_rack',
            'view_rack',
            'add_rackaccessory',
            'change_rackaccessory',
            'delete_rackaccessory',
            'view_rackaccessory',
            'add_serverroom',
            'change_serverroom',
            'delete_serverroom',
            'view_serverroom',
            'add_virtualserver',
            'change_virtualserver',
            'change_virtualserver_content_type_field',
            'change_virtualserver_parent_field',
            'change_virtualserver_remarks_field',
            'change_virtualserver_service_env_field',
            'change_virtualserver_tags_field',
            'delete_virtualserver',
            'view_virtualserver',
            'view_virtualserver_baseobject_ptr_field',
            'view_virtualserver_content_type_field',
            'view_virtualserver_id_field',
            'view_virtualserver_parent_field',
            'view_virtualserver_remarks_field',
            'view_virtualserver_service_env_field',
            'view_virtualserver_tags_field',
            'add_licence',
            'can_view_extra_baseobjectlicenceview',
            'can_view_extra_licenceadminattachmentsview',
            'can_view_extra_licenceuserview',
            'change_licence',
            'change_licence_accounting_id_field',
            'change_licence_base_objects_field',
            'change_licence_budget_info_field',
            'change_licence_content_type_field',
            'change_licence_invoice_date_field',
            'change_licence_invoice_no_field',
            'change_licence_licence_type_field',
            'change_licence_license_details_field',
            'change_licence_manufacturer_field',
            'change_licence_niw_field',
            'change_licence_number_bought_field',
            'change_licence_office_infrastructure_field',
            'change_licence_order_no_field',
            'change_licence_parent_field',
            'change_licence_price_field',
            'change_licence_property_of_field',
            'change_licence_provider_field',
            'change_licence_region_field',
            'change_licence_remarks_field',
            'change_licence_service_env_field',
            'change_licence_sn_field',
            'change_licence_software_field',
            'change_licence_tags_field',
            'change_licence_users_field',
            'change_licence_valid_thru_field',
            'delete_licence',
            'view_licence',
            'view_licence_accounting_id_field',
            'view_licence_baseobject_ptr_field',
            'view_licence_base_objects_field',
            'view_licence_budget_info_field',
            'view_licence_content_type_field',
            'view_licence_id_field',
            'view_licence_invoice_date_field',
            'view_licence_invoice_no_field',
            'view_licence_licence_type_field',
            'view_licence_license_details_field',
            'view_licence_manufacturer_field',
            'view_licence_niw_field',
            'view_licence_number_bought_field',
            'view_licence_office_infrastructure_field',
            'view_licence_order_no_field',
            'view_licence_parent_field',
            'view_licence_price_field',
            'view_licence_property_of_field',
            'view_licence_provider_field',
            'view_licence_region_field',
            'view_licence_remarks_field',
            'view_licence_service_env_field',
            'view_licence_sn_field',
            'view_licence_software_field',
            'view_licence_tags_field',
            'view_licence_users_field',
            'view_licence_valid_thru_field',
            'add_support',
            'can_view_extra_baseobjectsupportview',
            'can_view_extra_supportadminattachmentsview',
            'change_support',
            'change_support_asset_type_field',
            'change_support_base_objects_field',
            'change_support_budget_info_field',
            'change_support_content_type_field',
            'change_support_contract_id_field',
            'change_support_contract_terms_field',
            'change_support_date_from_field',
            'change_support_date_to_field',
            'change_support_description_field',
            'change_support_escalation_path_field',
            'change_support_invoice_date_field',
            'change_support_invoice_no_field',
            'change_support_name_field',
            'change_support_parent_field',
            'change_support_period_in_months_field',
            'change_support_price_field',
            'change_support_producer_field',
            'change_support_property_of_field',
            'change_support_region_field',
            'change_support_remarks_field',
            'change_support_serial_no_field',
            'change_support_service_env_field',
            'change_support_sla_type_field',
            'change_support_status_field',
            'change_support_supplier_field',
            'change_support_support_type_field',
            'change_support_tags_field',
            'delete_support',
            'view_support',
            'view_support_asset_type_field',
            'view_support_baseobject_ptr_field',
            'view_support_base_objects_field',
            'view_support_budget_info_field',
            'view_support_content_type_field',
            'view_support_contract_id_field',
            'view_support_contract_terms_field',
            'view_support_date_from_field',
            'view_support_date_to_field',
            'view_support_description_field',
            'view_support_escalation_path_field',
            'view_support_id_field',
            'view_support_invoice_date_field',
            'view_support_invoice_no_field',
            'view_support_name_field',
            'view_support_parent_field',
            'view_support_period_in_months_field',
            'view_support_price_field',
            'view_support_producer_field',
            'view_support_property_of_field',
            'view_support_region_field',
            'view_support_remarks_field',
            'view_support_serial_no_field',
            'view_support_service_env_field',
            'view_support_sla_type_field',
            'view_support_status_field',
            'view_support_supplier_field',
            'view_support_support_type_field',
            'view_support_tags_field'
        ]
        add_user_and_group('dc', 'dc', 'Data Center Group', dc_permissions)

        bo_permissions = [
            'can_view_extra_assetrelationsreport',
            'can_view_extra_attachmentsview',
            'can_view_extra_baserelationsreport',
            'can_view_extra_categorymodelreport',
            'can_view_extra_categorymodelstatusreport',
            'can_view_extra_licencerelationsreport',
            'can_view_extra_manufacturercategorymodelreport',
            'can_view_extra_multiaddview',
            'can_view_extra_ralphdetailview',
            'can_view_extra_ralphdetailviewadmin',
            'can_view_extra_ralphlistview',
            'can_view_extra_ralphtemplateview',
            'can_view_extra_reportdetail',
            'can_view_extra_runbulktransitionview',
            'can_view_extra_runtransitionview',
            'can_view_extra_statusmodelreport',
            'can_view_extra_userprofileview',
            'can_view_extra_usertransitionhistoryview',
            'view_ralphuser',
            'view_region',
            'add_asset',
            'change_asset',
            'change_asset_barcode_field',
            'change_asset_budget_info_field',
            'change_asset_content_type_field',
            'change_asset_depreciation_end_date_field',
            'change_asset_depreciation_rate_field',
            'change_asset_force_depreciation_field',
            'change_asset_hostname_field',
            'change_asset_invoice_date_field',
            'change_asset_invoice_no_field',
            'change_asset_model_field',
            'change_asset_niw_field',
            'change_asset_order_no_field',
            'change_asset_parent_field',
            'change_asset_price_field',
            'change_asset_property_of_field',
            'change_asset_provider_field',
            'change_asset_remarks_field',
            'change_asset_required_support_field',
            'change_asset_service_env_field',
            'change_asset_sn_field',
            'change_asset_tags_field',
            'change_asset_task_url_field',
            'delete_asset',
            'view_asset',
            'view_asset_barcode_field',
            'view_asset_baseobject_ptr_field',
            'view_asset_budget_info_field',
            'view_asset_content_type_field',
            'view_asset_depreciation_end_date_field',
            'view_asset_depreciation_rate_field',
            'view_asset_force_depreciation_field',
            'view_asset_hostname_field',
            'view_asset_id_field',
            'view_asset_invoice_date_field',
            'view_asset_invoice_no_field',
            'view_asset_model_field',
            'view_asset_niw_field',
            'view_asset_order_no_field',
            'view_asset_parent_field',
            'view_asset_price_field',
            'view_asset_property_of_field',
            'view_asset_provider_field',
            'view_asset_remarks_field',
            'view_asset_required_support_field',
            'view_asset_service_env_field',
            'view_asset_sn_field',
            'view_asset_tags_field',
            'view_asset_task_url_field',
            'add_assetholder',
            'change_assetholder',
            'delete_assetholder',
            'view_assetholder',
            'add_assetmodel',
            'change_assetmodel',
            'change_assetmodel_category_field',
            'change_assetmodel_cores_count_field',
            'change_assetmodel_has_parent_field',
            'change_assetmodel_height_of_device_field',
            'change_assetmodel_manufacturer_field',
            'change_assetmodel_name_field',
            'change_assetmodel_power_consumption_field',
            'change_assetmodel_type_field',
            'change_assetmodel_visualization_layout_back_field',
            'change_assetmodel_visualization_layout_front_field',
            'delete_assetmodel',
            'view_assetmodel',
            'view_assetmodel_category_field',
            'view_assetmodel_cores_count_field',
            'view_assetmodel_has_parent_field',
            'view_assetmodel_height_of_device_field',
            'view_assetmodel_id_field',
            'view_assetmodel_manufacturer_field',
            'view_assetmodel_name_field',
            'view_assetmodel_power_consumption_field',
            'view_assetmodel_type_field',
            'view_assetmodel_visualization_layout_back_field',
            'view_assetmodel_visualization_layout_front_field',
            'add_baseobject',
            'change_baseobject',
            'change_baseobject_content_type_field',
            'change_baseobject_parent_field',
            'change_baseobject_remarks_field',
            'change_baseobject_service_env_field',
            'change_baseobject_tags_field',
            'delete_baseobject',
            'view_baseobject',
            'view_baseobject_content_type_field',
            'view_baseobject_id_field',
            'view_baseobject_parent_field',
            'view_baseobject_remarks_field',
            'view_baseobject_service_env_field',
            'view_baseobject_tags_field',
            'add_budgetinfo',
            'change_budgetinfo',
            'delete_budgetinfo',
            'view_budgetinfo',
            'add_category',
            'change_category',
            'delete_category',
            'view_category',
            'add_manufacturer',
            'change_manufacturer',
            'delete_manufacturer',
            'view_manufacturer',
            'add_profitcenter',
            'change_profitcenter',
            'delete_profitcenter',
            'view_profitcenter',
            'add_attachment',
            'change_attachment',
            'delete_attachment',
            'view_attachment',
            'add_attachmentitem',
            'change_attachmentitem',
            'delete_attachmentitem',
            'view_attachmentitem',
            'add_backofficeasset',
            'can_view_extra_backofficeassetadminattachmentsview',
            'can_view_extra_backofficeassetcomponents',
            'can_view_extra_backofficeassetlicence',
            'can_view_extra_backofficeassetsoftware',
            'can_view_extra_backofficeassetsupport',
            'change_backofficeasset',
            'change_backofficeasset_barcode_field',
            'change_backofficeasset_budget_info_field',
            'change_backofficeasset_content_type_field',
            'change_backofficeasset_depreciation_end_date_field',
            'change_backofficeasset_depreciation_rate_field',
            'change_backofficeasset_force_depreciation_field',
            'change_backofficeasset_hostname_field',
            'change_backofficeasset_imei_field',
            'change_backofficeasset_invoice_date_field',
            'change_backofficeasset_invoice_no_field',
            'change_backofficeasset_loan_end_date_field',
            'change_backofficeasset_location_field',
            'change_backofficeasset_model_field',
            'change_backofficeasset_niw_field',
            'change_backofficeasset_office_infrastructure_field',
            'change_backofficeasset_order_no_field',
            'change_backofficeasset_owner_field',
            'change_backofficeasset_parent_field',
            'change_backofficeasset_price_field',
            'change_backofficeasset_property_of_field',
            'change_backofficeasset_provider_field',
            'change_backofficeasset_purchase_order_field',
            'change_backofficeasset_region_field',
            'change_backofficeasset_remarks_field',
            'change_backofficeasset_required_support_field',
            'change_backofficeasset_service_env_field',
            'change_backofficeasset_sn_field',
            'change_backofficeasset_status_field',
            'change_backofficeasset_tags_field',
            'change_backofficeasset_task_url_field',
            'change_backofficeasset_user_field',
            'change_backofficeasset_warehouse_field',
            'delete_backofficeasset',
            'view_backofficeasset',
            'view_backofficeasset_asset_ptr_field',
            'view_backofficeasset_barcode_field',
            'view_backofficeasset_baseobject_ptr_field',
            'view_backofficeasset_budget_info_field',
            'view_backofficeasset_content_type_field',
            'view_backofficeasset_depreciation_end_date_field',
            'view_backofficeasset_depreciation_rate_field',
            'view_backofficeasset_force_depreciation_field',
            'view_backofficeasset_hostname_field',
            'view_backofficeasset_id_field',
            'view_backofficeasset_imei_field',
            'view_backofficeasset_invoice_date_field',
            'view_backofficeasset_invoice_no_field',
            'view_backofficeasset_loan_end_date_field',
            'view_backofficeasset_location_field',
            'view_backofficeasset_model_field',
            'view_backofficeasset_niw_field',
            'view_backofficeasset_office_infrastructure_field',
            'view_backofficeasset_order_no_field',
            'view_backofficeasset_owner_field',
            'view_backofficeasset_parent_field',
            'view_backofficeasset_price_field',
            'view_backofficeasset_property_of_field',
            'view_backofficeasset_provider_field',
            'view_backofficeasset_purchase_order_field',
            'view_backofficeasset_region_field',
            'view_backofficeasset_remarks_field',
            'view_backofficeasset_required_support_field',
            'view_backofficeasset_service_env_field',
            'view_backofficeasset_sn_field',
            'view_backofficeasset_status_field',
            'view_backofficeasset_tags_field',
            'view_backofficeasset_task_url_field',
            'view_backofficeasset_user_field',
            'view_backofficeasset_warehouse_field',
            'add_officeinfrastructure',
            'change_officeinfrastructure',
            'delete_officeinfrastructure',
            'view_officeinfrastructure',
            'add_warehouse',
            'change_warehouse',
            'delete_warehouse',
            'view_warehouse',
            'add_baseobjectlicence',
            'change_baseobjectlicence',
            'delete_baseobjectlicence',
            'view_baseobjectlicence',
            'add_licence',
            'can_view_extra_baseobjectlicenceview',
            'can_view_extra_licenceadminattachmentsview',
            'can_view_extra_licenceuserview',
            'change_licence',
            'change_licence_accounting_id_field',
            'change_licence_base_objects_field',
            'change_licence_budget_info_field',
            'change_licence_content_type_field',
            'change_licence_invoice_date_field',
            'change_licence_invoice_no_field',
            'change_licence_licence_type_field',
            'change_licence_license_details_field',
            'change_licence_manufacturer_field',
            'change_licence_niw_field',
            'change_licence_number_bought_field',
            'change_licence_office_infrastructure_field',
            'change_licence_order_no_field',
            'change_licence_parent_field',
            'change_licence_price_field',
            'change_licence_property_of_field',
            'change_licence_provider_field',
            'change_licence_region_field',
            'change_licence_remarks_field',
            'change_licence_service_env_field',
            'change_licence_sn_field',
            'change_licence_software_field',
            'change_licence_tags_field',
            'change_licence_users_field',
            'change_licence_valid_thru_field',
            'delete_licence',
            'view_licence',
            'view_licence_accounting_id_field',
            'view_licence_baseobject_ptr_field',
            'view_licence_base_objects_field',
            'view_licence_budget_info_field',
            'view_licence_content_type_field',
            'view_licence_id_field',
            'view_licence_invoice_date_field',
            'view_licence_invoice_no_field',
            'view_licence_licence_type_field',
            'view_licence_license_details_field',
            'view_licence_manufacturer_field',
            'view_licence_niw_field',
            'view_licence_number_bought_field',
            'view_licence_office_infrastructure_field',
            'view_licence_order_no_field',
            'view_licence_parent_field',
            'view_licence_price_field',
            'view_licence_property_of_field',
            'view_licence_provider_field',
            'view_licence_region_field',
            'view_licence_remarks_field',
            'view_licence_service_env_field',
            'view_licence_sn_field',
            'view_licence_software_field',
            'view_licence_tags_field',
            'view_licence_users_field',
            'view_licence_valid_thru_field',
            'add_licencetype',
            'change_licencetype',
            'change_licencetype_name_field',
            'delete_licencetype',
            'view_licencetype',
            'view_licencetype_id_field',
            'view_licencetype_name_field',
            'add_licenceuser',
            'change_licenceuser',
            'delete_licenceuser',
            'view_licenceuser',
            'add_reportlanguage',
            'change_reportlanguage',
            'delete_reportlanguage',
            'view_reportlanguage',
            'add_reporttemplate',
            'change_reporttemplate',
            'delete_reporttemplate',
            'view_reporttemplate',
            'add_baseobjectssupport',
            'change_baseobjectssupport',
            'delete_baseobjectssupport',
            'view_baseobjectssupport',
            'add_support',
            'can_view_extra_baseobjectsupportview',
            'can_view_extra_supportadminattachmentsview',
            'change_support',
            'change_support_asset_type_field',
            'change_support_base_objects_field',
            'change_support_budget_info_field',
            'change_support_content_type_field',
            'change_support_contract_id_field',
            'change_support_contract_terms_field',
            'change_support_date_from_field',
            'change_support_date_to_field',
            'change_support_description_field',
            'change_support_escalation_path_field',
            'change_support_invoice_date_field',
            'change_support_invoice_no_field',
            'change_support_name_field',
            'change_support_parent_field',
            'change_support_period_in_months_field',
            'change_support_price_field',
            'change_support_producer_field',
            'change_support_property_of_field',
            'change_support_region_field',
            'change_support_remarks_field',
            'change_support_serial_no_field',
            'change_support_service_env_field',
            'change_support_sla_type_field',
            'change_support_status_field',
            'change_support_supplier_field',
            'change_support_support_type_field',
            'change_support_tags_field',
            'delete_support',
            'view_support',
            'view_support_asset_type_field',
            'view_support_baseobject_ptr_field',
            'view_support_base_objects_field',
            'view_support_budget_info_field',
            'view_support_content_type_field',
            'view_support_contract_id_field',
            'view_support_contract_terms_field',
            'view_support_date_from_field',
            'view_support_date_to_field',
            'view_support_description_field',
            'view_support_escalation_path_field',
            'view_support_id_field',
            'view_support_invoice_date_field',
            'view_support_invoice_no_field',
            'view_support_name_field',
            'view_support_parent_field',
            'view_support_period_in_months_field',
            'view_support_price_field',
            'view_support_producer_field',
            'view_support_property_of_field',
            'view_support_region_field',
            'view_support_remarks_field',
            'view_support_serial_no_field',
            'view_support_service_env_field',
            'view_support_sla_type_field',
            'view_support_status_field',
            'view_support_supplier_field',
            'view_support_support_type_field',
            'view_support_tags_field',
            'add_supporttype',
            'change_supporttype',
            'delete_supporttype',
            'view_supporttype',
            'add_transition',
            'change_transition',
            'delete_transition',
            'view_transition'
        ]

        add_user_and_group('bo', 'bo', 'Back Office Group', bo_permissions)

    def generate_transitions(self):
        self.stdout.write('Generating Transitions')

        def add_transition(content_type, name, source, target, actions):
            transition, _ = Transition.objects.get_or_create(
                model=TransitionModel.objects.get(
                    content_type=content_type
                ),
                name=name,
                source=source,
                target=target
            )
            for action in actions:
                transition.actions.add(
                    Action.objects.get(
                        name=action, content_type=content_type
                    )
                )

        report = Report.objects.create(name='release')
        language = ReportLanguage.objects.create(name='en', default=True)
        report_template = ReportTemplate.objects.create(
            language=language,
            default=True,
            report=report
        )
        with open(
            os.path.join(settings.BASE_DIR, 'data_importer/data/release.odt'),
            'rb'
        ) as f:
            report_template.template.save('release.odt', File(f))

        bo_content_type = ContentType.objects.get_for_model(BackOfficeAsset)
        add_transition(
            bo_content_type,
            'Deploy',
            [
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.used.id,
                BackOfficeAssetStatus.loan.id,
                BackOfficeAssetStatus.damaged.id,
                BackOfficeAssetStatus.in_service.id,
                BackOfficeAssetStatus.installed.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id
            ],
            BackOfficeAssetStatus.in_progress.id,
            ['assign_licence', 'assign_user', 'assign_owner']
        )
        add_transition(
            bo_content_type,
            'Release asset',
            [
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id
            ],
            BackOfficeAssetStatus.used.id,
            [
                'assign_user', 'assign_owner', 'assign_warehouse',
                'release_report'
            ]
        )
        add_transition(
            bo_content_type,
            'Loan asset',
            [
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id
            ],
            BackOfficeAssetStatus.loan.id,
            [
                'assign_loan_end_date', 'assign_user', 'assign_owner',
                'assign_warehouse', 'assign_task_url'
            ]
        )
        add_transition(
            bo_content_type,
            'Buyout',
            [i[0] for i in BackOfficeAssetStatus()],
            BackOfficeAssetStatus.liquidated.id,
            [
                'assign_task_url', 'assign_warehouse', 'assign_warehouse',
                'unassign_licences', 'unassign_loan_end_date',
                'unassign_owner',
            ]
        )

        dc_content_type = ContentType.objects.get_for_model(DataCenterAsset)

        add_transition(
            dc_content_type,
            'Change rack',
            [
                DataCenterAssetStatus.free.id,
                DataCenterAssetStatus.new.id,
                DataCenterAssetStatus.to_deploy.id,
            ],
            DataCenterAssetStatus.used.id,
            ['change_rack']
        )

    def generate_licence(self):
        self.stdout.write('Generating Licences')
        for i in range(self.object_limit):
            licence = LicenceFactory()
            LicenceUser.objects.create(
                licence=licence,
                user=self.get_user()
            )
            for j in range(3):
                back_office_asset = BaseObjectLicenceFactory(
                    licence=licence
                ).base_object
                back_office_asset.owner = self.get_user()
                back_office_asset.user = self.get_user()
                back_office_asset.save()

            licence = LicenceFactory()
            LicenceUser.objects.create(
                licence=licence,
                user=self.get_user()
            )
            for j in range(3):
                DataCenterAssetLicenceFactory(
                    licence=licence
                )

    def generate_users(self):
        for i in range(self.object_limit):
            UserFactory()
        return RalphUser.objects.all()

    def get_user(self):
        if not getattr(self, 'users', False):
            self.users = cycle(self.generate_users())
        return next(self.users)

    def generate_support(self):
        self.stdout.write('Generating Supports')
        for i in range(self.object_limit):
            # BaseObjectsSupportFactory automatically generates Support
            for j in range(3):
                back_office_asset = BaseObjectsSupportFactory().baseobject
                back_office_asset.owner = self.get_user()
                back_office_asset.user = self.get_user()
                back_office_asset.save()

    def handle(self, *args, **options):
        apps = options.get('apps').split(',')
        if 'all' in apps:
            apps = self.all_apps

        if options.get('flush', False):
            self.stdout.write('Flush database..')
            call_command('flush', interactive=False)
            self.stdout.write('Flush finished.')

        self.generate_users_and_groups()

        if 'backoffice' in apps:
            self.generate_back_office()
        if 'datacenter' in apps:
            self.generate_data_center()
        if 'supports' in apps:
            self.generate_support()
        if 'licences' in apps:
            self.generate_licence()
        if 'transitions' in apps:
            self.generate_transitions()

        # Create super user
        root = UserFactory(username='ralph', is_superuser=True, is_staff=True)
        root.set_password('ralph')
        root.save()

        if options.get('flush', False):
            call_command('sitetree_resync_apps', interactive=False)
        self.stdout.write('done')
