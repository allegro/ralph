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
    BusinessSegmentFactory,
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
from ralph.data_importer.management.commands.create_transitions import \
    Command as TransitionCommand
from ralph.licences.models import LicenceUser
from ralph.licences.tests.factories import (
    BaseObjectLicenceFactory,
    DataCenterAssetLicenceFactory,
    LicenceFactory
)
from ralph.reports.models import Report, ReportLanguage, ReportTemplate
from ralph.supports.tests.factories import BaseObjectsSupportFactory
from ralph.virtual.tests.factories import CloudImageFactory


def get_imei(n):
    """Random IMEI generator. This function return random but not unique
    IMEI number. Based on code from http://stackoverflow.com/a/20733310
    """

    def luhn_residue(digits):
        """Luhn algorithm"""
        return (
            sum(
                sum(divmod(int(d) * (1 + i % 2), 10))
                for i, d in enumerate(digits[::-1])
            )
            % 10
        )

    part = "".join(str(random.randrange(0, 9)) for _ in range(n - 1))
    res = luhn_residue("{}{}".format(part, 0))
    return "{}{}".format(part, -res % 10)


class Command(BaseCommand):
    help = "Generating demo data."
    all_apps = [
        "backoffice",
        "datacenter",
        "licences",
        "supports",
        "transitions",
        "sim_cards",
        "cloudimages",
    ]
    object_limit = 30

    def add_arguments(self, parser):
        parser.add_argument(
            "-a",
            "--apps",
            choices=self.all_apps + ["all"],
            default="all",
            dest="apps",
            help="One or more apps separated by comma.",
        )
        parser.add_argument(
            "-f",
            "--flush",
            default=False,
            action="store_true",
            dest="flush",
            help="Flush database before generate.",
        )

    def generate_data_center(self):
        self.stdout.write("Generating Data Center assets")
        data_center_status = DataCenterAssetStatus()
        parent_category = DataCenterCategoryFactory(
            name="DATA CENTER", imei_required=False
        )
        for i in range(2):
            server_room = ServerRoomFactory()
            visualization_col = 1
            visualization_row = 1
            for j in range(10):
                rack = RackFactory(
                    server_room=server_room,
                    visualization_row=visualization_row,
                    visualization_col=visualization_col,
                )
                visualization_row += 1
                if visualization_row > server_room.visualization_rows_num:
                    visualization_row = 1
                    visualization_col += 1

                accessory = AccessoryFactory()
                RackAccessoryFactory(rack=rack, accessory=accessory)
                position = 1
                for status_id, name in data_center_status:
                    for i in range(2):
                        asset_model = DataCenterAssetModelFactory(
                            category=DataCenterCategoryFactory(parent=parent_category)
                        )
                        DataCenterAssetFactory(
                            rack=rack,
                            status=status_id,
                            position=position,
                            slot_no="",
                            service_env=ServiceEnvironmentFactory(),
                            model=asset_model,
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
                    name="Chassis",
                    category=DataCenterCategoryFactory(parent=parent_category),
                    height_of_device=5,
                ),
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
                        name="Blade",
                        has_parent=True,
                        category=DataCenterCategoryFactory(parent=parent_category),
                    ),
                )

    def generate_back_office(self):
        self.stdout.write("Generating Back Office assets")
        back_office_status = BackOfficeAssetStatus()
        per_page = 2
        parent_category = CategoryFactory(name="BACK OFFICE", imei_required=False)
        for i in range(3):
            ProfitCenterFactory()
            BusinessSegmentFactory()

        for status_id, name in back_office_status:
            for i in range(int(per_page)):
                BackOfficeAssetFactory(
                    status=status_id,
                    user=self.get_user(),
                    owner=self.get_user(),
                    model=BackOfficeAssetModelFactory(
                        category=CategoryFactory(parent=parent_category)
                    ),
                )
                BackOfficeAssetFactory(
                    status=status_id,
                    user=self.get_user(),
                    owner=self.get_user(),
                    model=BackOfficeAssetModelFactory(
                        category=CategoryFactory(
                            name="Mobile Phone",
                            imei_required=True,
                            parent=parent_category,
                        ),
                        name="Phone",
                    ),
                    imei=get_imei(15),
                    imei2=get_imei(15),
                )

    def generate_users_and_groups(self):
        self.stdout.write("Generating Users and Groups")

        def add_user_and_group(username, password, group_name, permission_models):
            group = GroupFactory(name=group_name)
            for permision_model in permission_models:
                for perm in Permission.objects.filter(
                    content_type=ContentType.objects.get_by_natural_key(
                        *permision_model.split(".")
                    )
                ):
                    group.permissions.add(perm)

            user = UserFactory(username=username, is_staff=True)
            user.regions.add(RegionFactory())
            user.set_password(password)
            user.groups.add(group)
            user.save()

        dc_permission_models = [
            "accounts.region",
            "assets.assetmodel",
            "assets.environment",
            "assets.service",
            "assets.serviceenvironment",
            "data_center.accessory",
            "data_center.database",
            "data_center.datacenter",
            "data_center.datacenterasset",
            "data_center.rack",
            "data_center.rackaccessory",
            "data_center.serverroom",
            "licences.licence",
            "networks.ipaddress",
            "supports.support",
            "virtual.virtualserver",
        ]
        add_user_and_group("dc", "dc", "Data Center Group", dc_permission_models)

        bo_permission_models = [
            "accounts.ralphuser",
            "accounts.region",
            "assets.asset",
            "assets.assetholder",
            "assets.assetmodel",
            "assets.baseobject",
            "assets.budgetinfo",
            "assets.category",
            "assets.manufacturer",
            "assets.profitcenter",
            "attachments.attachment",
            "attachments.attachmentitem",
            "back_office.backofficeasset",
            "back_office.officeinfrastructure",
            "back_office.warehouse",
            "licences.baseobjectlicence",
            "licences.licence",
            "licences.licencetype",
            "licences.licenceuser",
            "reports.reportlanguage",
            "reports.reporttemplate",
            "supports.baseobjectssupport",
            "supports.support",
            "supports.supporttype",
            "transitions.transition",
        ]

        add_user_and_group("bo", "bo", "Back Office Group", bo_permission_models)

    def generate_transitions(self):
        self.stdout.write("Generating Transitions")

        report = Report.objects.create(name="release")
        language = ReportLanguage.objects.create(name="en", default=True)
        report_template = ReportTemplate.objects.create(
            language=language, default=True, report=report
        )
        with open(
            os.path.join(settings.BASE_DIR, "data_importer/data/release.odt"), "rb"
        ) as f:
            report_template.template.save("release.odt", File(f))

        bo_content_type = ContentType.objects.get_for_model(BackOfficeAsset)
        TransitionCommand.add_transition(
            content_type=bo_content_type,
            name="Deploy",
            source=[
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.used.id,
                BackOfficeAssetStatus.loan.id,
                BackOfficeAssetStatus.damaged.id,
                BackOfficeAssetStatus.in_service.id,
                BackOfficeAssetStatus.installed.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id,
            ],
            target=BackOfficeAssetStatus.in_progress.id,
            actions=["assign_licence", "assign_user", "assign_owner"],
        )
        TransitionCommand.add_transition(
            content_type=bo_content_type,
            name="Release asset",
            source=[
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id,
            ],
            target=BackOfficeAssetStatus.used.id,
            actions=[
                "assign_user",
                "assign_owner",
                "assign_warehouse",
                "release_report",
            ],
        )
        TransitionCommand.add_transition(
            content_type=bo_content_type,
            name="Loan asset",
            source=[
                BackOfficeAssetStatus.new.id,
                BackOfficeAssetStatus.in_progress.id,
                BackOfficeAssetStatus.waiting_for_release.id,
                BackOfficeAssetStatus.free.id,
                BackOfficeAssetStatus.reserved.id,
            ],
            target=BackOfficeAssetStatus.loan.id,
            actions=[
                "assign_loan_end_date",
                "assign_user",
                "assign_owner",
                "assign_warehouse",
                "assign_task_url",
            ],
        )
        TransitionCommand.add_transition(
            content_type=bo_content_type,
            name="Buyout",
            source=[i[0] for i in BackOfficeAssetStatus()],
            target=BackOfficeAssetStatus.liquidated.id,
            actions=[
                "assign_task_url",
                "assign_warehouse",
                "assign_warehouse",
                "unassign_licences",
                "unassign_loan_end_date",
                "unassign_owner",
            ],
        )

        dc_content_type = ContentType.objects.get_for_model(DataCenterAsset)

        TransitionCommand.add_transition(
            content_type=dc_content_type,
            name="Change rack",
            source=[
                DataCenterAssetStatus.free.id,
                DataCenterAssetStatus.new.id,
                DataCenterAssetStatus.to_deploy.id,
            ],
            target=DataCenterAssetStatus.used.id,
            actions=["change_rack"],
        )

    def generate_licence(self):
        self.stdout.write("Generating Licences")
        for i in range(self.object_limit):
            licence = LicenceFactory()
            LicenceUser.objects.create(licence=licence, user=self.get_user())
            for j in range(3):
                back_office_asset = BaseObjectLicenceFactory(
                    licence=licence
                ).base_object
                back_office_asset.owner = self.get_user()
                back_office_asset.user = self.get_user()
                back_office_asset.save()

            licence = LicenceFactory()
            LicenceUser.objects.create(licence=licence, user=self.get_user())
            for j in range(3):
                DataCenterAssetLicenceFactory(licence=licence)

    def generate_users(self):
        for i in range(self.object_limit):
            UserFactory()
        return RalphUser.objects.all()

    def get_user(self):
        if not getattr(self, "users", False):
            self.users = cycle(self.generate_users())
        return next(self.users)

    def generate_support(self):
        self.stdout.write("Generating Supports")
        for i in range(self.object_limit):
            # BaseObjectsSupportFactory automatically generates Support
            for j in range(3):
                back_office_asset = BaseObjectsSupportFactory().baseobject
                back_office_asset.owner = self.get_user()
                back_office_asset.user = self.get_user()
                back_office_asset.save()

    def generate_cloud_images(self):
        self.stdout.write("Generating Cloud Images")
        for i in range(self.object_limit):
            CloudImageFactory()

    def handle(self, *args, **options):
        apps = options.get("apps").split(",")
        if "all" in apps:
            apps = self.all_apps

        if options.get("flush", False):
            self.stdout.write("Flush database..")
            call_command("flush", interactive=False)
            self.stdout.write("Flush finished.")

        self.generate_users_and_groups()

        if "backoffice" in apps:
            self.generate_back_office()
        if "datacenter" in apps:
            self.generate_data_center()
        if "supports" in apps:
            self.generate_support()
        if "licences" in apps:
            self.generate_licence()
        if "transitions" in apps:
            self.generate_transitions()
        if "cloudimages" in apps:
            self.generate_cloud_images()

        # Create super user
        root = UserFactory(username="ralph", is_superuser=True, is_staff=True)
        root.set_password("ralph")
        root.save()

        if options.get("flush", False):
            call_command("sitetree_resync_apps", interactive=False)
        self.stdout.write("done")
