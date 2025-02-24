# -*- coding: utf-8 -*-
from datetime import datetime
from unittest.mock import patch

from dj.choices import Country
from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings, RequestFactory, SimpleTestCase
from django.urls import reverse
from django.utils import timezone

import ralph.back_office.models
from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.country_utils import iso2_to_iso3, iso3_to_iso2
from ralph.assets.models import AssetLastHostname, ObjectModelType
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    CategoryFactory,
    DataCenterAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.attachments.models import Attachment
from ralph.back_office.helpers import EmailContext
from ralph.back_office.models import (
    _check_assets_owner,
    BackOfficeAsset,
    BackOfficeAssetStatus
)
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models import DataCenterAsset, DataCenterAssetStatus
from ralph.data_center.tests.factories import RackFactory
from ralph.lib.external_services import ExternalService
from ralph.lib.transitions.models import (
    _check_instances_for_transition,
    run_field_transition,
    Transition,
    TransitionModel,
    TransitionNotAllowedError
)
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.licences.tests.factories import LicenceFactory
from ralph.reports.factories import ReportTemplateFactory
from ralph.reports.helpers import generate_report
from ralph.tests import RalphTestCase
from ralph.tests.factories import UserFactory
from ralph.tests.mixins import ClientMixin


class HostnameGeneratorTests(RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region_pl = RegionFactory(name="PL", country=Country.pl)
        cls.region_pl.country = Country.pl
        cls.region_pl.save()

    def _check_hostname_not_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertIsNone(changed_asset.hostname)

    def _check_hostname_is_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertTrue(len(changed_asset.hostname) > 0)

    def test_generate_first_hostname(self):
        """Scenario:
        - none of assets has hostname
        - after generate first of asset have XXXYY00001 in hostname field
        """
        category = CategoryFactory(code="PC")
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, hostname="")
        template_vars = {
            "code": asset.model.category.code,
            "country_code": asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, "POLPC00001")

    def test_generate_next_hostname(self):
        category = CategoryFactory(code="PC")
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, region=self.region_pl, hostname="")
        BackOfficeAssetFactory(region=self.region_pl, hostname="POLSW00003")
        AssetLastHostname.increment_hostname(prefix="POLPC")
        AssetLastHostname.increment_hostname(prefix="POLPC")
        template_vars = {
            "code": asset.model.category.code,
            "country_code": asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, "POLPC00003")

    def test_cant_generate_hostname_for_model_without_category(self):
        model = BackOfficeAssetModelFactory(category=None)
        asset = BackOfficeAssetFactory(model=model, region=self.region_pl, hostname="")
        self._check_hostname_not_generated(asset)

    def test_can_generate_hostname_for_model_with_hostname(self):
        category = CategoryFactory(code="PC")
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, region=self.region_pl)
        self._check_hostname_is_generated(asset)

    def test_generate_next_hostname_out_of_range(self):
        category = CategoryFactory(code="PC")
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, region=self.region_pl, hostname="")
        AssetLastHostname.objects.create(prefix="POLPC", counter=99999)
        template_vars = {
            "code": asset.model.category.code,
            "country_code": asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, "POLPC100000")

    def test_convert_iso2_to_iso3(self):
        self.assertEqual(iso2_to_iso3("PL"), "POL")

    def test_convert_iso3_to_iso2(self):
        self.assertEqual(iso3_to_iso2("POL"), "PL")

    def test_validate_imei(self):
        bo_asset_failed = BackOfficeAssetFactory(imei="failed", imei2="failed")
        bo_asset = BackOfficeAssetFactory(
            imei="990000862471854", imei2="990000862471854"
        )

        self.assertFalse(bo_asset_failed.validate_imei(bo_asset_failed.imei))
        self.assertTrue(bo_asset.validate_imei(bo_asset.imei))

        self.assertFalse(bo_asset_failed.validate_imei(bo_asset_failed.imei2))
        self.assertTrue(bo_asset.validate_imei(bo_asset.imei2))


class TestBackOfficeAsset(RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region_pl = RegionFactory(name="PL", country=Country.pl)
        cls.region_us = RegionFactory(name="US", country=Country.us)
        cls.category = CategoryFactory(code="PC")
        cls.category_without_code = CategoryFactory()
        cls.model = BackOfficeAssetModelFactory(category=cls.category)
        cls.model_without_code = BackOfficeAssetModelFactory(
            category=cls.category_without_code
        )

    def setUp(self):
        with override_settings(
            ASSET_BUYOUT_CATEGORY_TO_MONTHS={str(self.category.pk): 48}
        ):
            super().setUp()
            AssetLastHostname.objects.create(prefix="POLPC", counter=1000)
            self.bo_asset = BackOfficeAssetFactory(
                model=self.model,
                hostname="abc",
                region=self.region_pl,
            )
            self.bo_asset_2 = BackOfficeAssetFactory(
                model=self.model,
                hostname="abc2",
                region=self.region_pl,
                status=BackOfficeAssetStatus.liquidated.id,
                invoice_date=None,
            )
            self.bo_asset_3 = BackOfficeAssetFactory(
                model=self.model,
                hostname="abc3",
                region=self.region_pl,
                status=BackOfficeAssetStatus.liquidated.id,
                invoice_date=datetime(2016, 1, 11).date(),
                depreciation_rate=50,
            )
            self.bo_asset_4 = BackOfficeAssetFactory(
                model=self.model,
                hostname="abc3",
                region=self.region_pl,
                status=BackOfficeAssetStatus.liquidated.id,
                invoice_date=datetime(2016, 1, 11).date(),
                depreciation_end_date=datetime(2015, 1, 11).date(),
                depreciation_rate=50,
            )
            self.category_parent = CategoryFactory(
                code="Mob1", default_depreciation_rate=30
            )
            self.category_2 = CategoryFactory(code="Mob2", default_depreciation_rate=25)
            self.category_3 = CategoryFactory(
                code="Mob3", parent=self.category_parent, default_depreciation_rate=0
            )

    def test_try_assign_hostname(self):
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, "POLPC01001")

    def test_try_assign_hostname_no_change(self):
        self.bo_asset.hostname = "POLPC01001"
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, "POLPC01001")

    def test_try_assign_hostname_no_hostname(self):
        self.bo_asset.hostname = ""
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, "POLPC01001")

    def test_try_assign_hostname_forced(self):
        self.bo_asset.hostname = "POLPC001010"
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.assertEqual(self.bo_asset.hostname, "POLPC01001")

    def test_try_assign_hostname_with_country(self):
        self.bo_asset._try_assign_hostname(country="US", commit=True)
        self.assertEqual(self.bo_asset.hostname, "USPC00001")

    def test_try_assign_hostname_category_without_code(self):
        bo_asset_2 = BackOfficeAssetFactory(
            model=self.model_without_code, hostname="abcd"
        )
        bo_asset_2._try_assign_hostname(commit=True)
        self.assertEqual(bo_asset_2.hostname, "abcd")

    def test_get_autocomplete_queryset(self):
        queryset = BackOfficeAsset.get_autocomplete_queryset()
        self.assertEqual(1, queryset.count())

    def test_buyout_date(self):
        self.assertEqual(self.bo_asset_3.buyout_date, datetime(2020, 1, 11).date())

        self.assertEqual(self.bo_asset_2.buyout_date, None)

    def test_buyout_date_doesnt_use_depreciation_end_date(self):
        self.assertEqual(self.bo_asset_4.buyout_date, datetime(2020, 1, 11).date())

    def test_changing_buyout_date(self):
        new_date = datetime(2020, 5, 11).date()
        self.bo_asset_3.buyout_date = new_date
        self.bo_asset_3.save()
        self.bo_asset_3.refresh_from_db()
        self.assertEqual(self.bo_asset_3.buyout_date, new_date)

    def test_get_depreciation_rate(self):
        self.assertEqual(self.category_2.get_default_depreciation_rate(), 25)
        self.assertEqual(self.category_3.get_default_depreciation_rate(), 30)


class TestBackOfficeAssetTransitions(TransitionTestCase, RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(country=Country.pl)
        cls.region_pl = RegionFactory(name="PL", country=Country.pl)
        cls.region_us = RegionFactory(name="US", country=Country.us)
        cls.region_us_2 = RegionFactory(name="US", country=Country.us)
        cls.category = CategoryFactory(code="PC")
        cls.model = BackOfficeAssetModelFactory(category=cls.category)

    def setUp(self):
        super().setUp()
        AssetLastHostname.objects.create(prefix="POLPC", counter=1000)
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname="abc",
            region=self.region_us,
        )
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.request = RequestFactory().get("/assets/")
        self.request.user = self.user_pl
        # ugly hack from https://code.djangoproject.com/ticket/17971
        setattr(self.request, "session", "session")
        messages = FallbackStorage(self.request)
        setattr(self.request, "_messages", messages)

    def test_convert_to_data_center_asset(self):
        bo_asset = BackOfficeAssetFactory()
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(bo_asset, "status"),
            source=0,
            target=0,
        )
        bo_asset_pk = bo_asset.pk
        hostname = bo_asset.hostname
        rack = RackFactory()
        BackOfficeAsset.convert_to_data_center_asset(
            instances=[bo_asset],
            rack=rack.id,
            service_env=ServiceEnvironmentFactory().id,
            position=1,
            model=DataCenterAssetModelFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        dc_asset = DataCenterAsset.objects.get(pk=bo_asset_pk)
        self.assertEqual(dc_asset.rack.id, rack.id)
        self.assertFalse(BackOfficeAsset.objects.filter(pk=bo_asset_pk).exists())
        self.assertEqual(dc_asset.hostname, hostname)

    def test_convert_to_data_center_asset_preserves_status_name(self):
        bo_asset = BackOfficeAssetFactory(
            status=BackOfficeAssetStatus.from_name("damaged")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(bo_asset, "status"),
            source=0,
            target=0,
        )
        bo_asset_pk = bo_asset.pk
        bo_asset_status_name = BackOfficeAssetStatus.from_id(bo_asset.status).name
        rack = RackFactory()
        BackOfficeAsset.convert_to_data_center_asset(
            instances=[bo_asset],
            rack=rack.id,
            service_env=ServiceEnvironmentFactory().id,
            position=1,
            model=DataCenterAssetModelFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        dc_asset = DataCenterAsset.objects.get(pk=bo_asset_pk)
        dc_asset_status_name = DataCenterAssetStatus.from_id(dc_asset.status).name
        self.assertEqual(bo_asset_status_name, dc_asset_status_name)

    def test_convert_to_data_center_asset_uses_default_from_transition(self):
        target_status_id = DataCenterAssetStatus.from_name(
            "new"  # status name common for dc_asset and bo_asset
        ).id
        bo_asset = BackOfficeAssetFactory(
            status=BackOfficeAssetStatus.from_name("damaged")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(bo_asset, "status"),
            source=0,
            target=target_status_id,
        )
        bo_asset_pk = bo_asset.pk
        target_status_name = BackOfficeAssetStatus.from_id(target_status_id).name
        rack = RackFactory()
        BackOfficeAsset.convert_to_data_center_asset(
            instances=[bo_asset],
            rack=rack.id,
            service_env=ServiceEnvironmentFactory().id,
            position=1,
            model=DataCenterAssetModelFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        dc_asset = DataCenterAsset.objects.get(pk=bo_asset_pk)
        dc_asset_status_name = DataCenterAssetStatus.from_id(dc_asset.status).name
        self.assertEqual(target_status_name, dc_asset_status_name)

    def test_convert_to_data_center_asset_uses_default_from_settings(self):
        target_status_id = DataCenterAssetStatus.from_id(
            settings.CONVERT_TO_DATACENTER_ASSET_DEFAULT_STATUS_ID
        ).id
        bo_asset = BackOfficeAssetFactory(
            status=BackOfficeAssetStatus.from_name("damaged")
        )
        transition = Transition.objects.create(
            name="transition",
            model=TransitionModel.get_for_field(bo_asset, "status"),
            source=0,
            target=target_status_id,
        )
        bo_asset_pk = bo_asset.pk
        target_status_name = BackOfficeAssetStatus.from_id(target_status_id).name
        rack = RackFactory()
        BackOfficeAsset.convert_to_data_center_asset(
            instances=[bo_asset],
            rack=rack.id,
            service_env=ServiceEnvironmentFactory().id,
            position=1,
            model=DataCenterAssetModelFactory().id,
            request=None,
            transition_id=transition.pk,
        )
        dc_asset = DataCenterAsset.objects.get(pk=bo_asset_pk)
        dc_asset_status_name = DataCenterAssetStatus.from_id(dc_asset.status).name
        self.assertEqual(target_status_name, dc_asset_status_name)

    def test_assign_many_licences(self):
        asset = BackOfficeAssetFactory()
        licences = [LicenceFactory() for i in range(2)]
        self.assertFalse(asset.licences.all())

        BackOfficeAsset.assign_licence(
            instances=[asset],
            request=None,
            licences=licences,
        )

        self.assertCountEqual(
            [base_obj_lic.licence.id for base_obj_lic in asset.licences.all()],
            [licence.id for licence in licences],
        )

    def test_change_hostname(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="test",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["change_hostname"],
        )
        run_field_transition(
            [self.bo_asset],
            field="status",
            transition_obj_or_name=transition,
            data={"change_hostname__country": Country.pl},
            requester=self.request.user,
        )
        self.assertEqual(self.bo_asset.hostname, "POLPC01001")

    def test_assign_owner(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="test",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["assign_owner"],
        )
        run_field_transition(
            [self.bo_asset],
            field="status",
            transition_obj_or_name=transition,
            data={"assign_owner__owner": self.user_pl.id},
            requester=self.request.user,
        )

    @override_settings(BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME=False)
    def test_assign_hostname_doesnt_assign_hostname_when_its_empty(self):
        hostname = ""
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname=hostname,
            region=self.region_us,
        )
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="assign_hostname_if_empty_or_country_not_match",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["assign_hostname_if_empty_or_country_not_match"],
        )
        self.assertEqual(self.bo_asset.hostname, hostname)

        run_field_transition(
            [self.bo_asset],
            field="status",
            transition_obj_or_name=transition,
            data={},
            requester=self.request.user,
        )

        self.assertEqual(self.bo_asset.hostname, hostname)

    @override_settings(BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME=True)
    def test_assign_hostname_assigns_hostname_when_its_empty(self):
        hostname = ""
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname=hostname,
            region=self.region_us,
        )
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="assign_hostname_if_empty_or_country_not_match",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["assign_hostname_if_empty_or_country_not_match"],
        )
        self.assertEqual(self.bo_asset.hostname, hostname)

        run_field_transition(
            [self.bo_asset],
            field="status",
            transition_obj_or_name=transition,
            data={},
            requester=self.request.user,
        )

        self.assertNotEquals(self.bo_asset.hostname, hostname)

    def test_assign_hostname_skips_hostname_when_its_already_set(self):
        # hostname must include country-code to be skipped during assigning
        hostname = "the-same-hostname-across-transitions-{}".format("USA")
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname=hostname,
            region=self.region_us,
        )
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="assign_hostname_if_empty_or_country_not_match",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["assign_hostname_if_empty_or_country_not_match"],
        )
        self.assertEqual(self.bo_asset.hostname, hostname)

        run_field_transition(
            [self.bo_asset],
            field="status",
            transition_obj_or_name=transition,
            data={},
            requester=self.request.user,
        )

        self.assertEqual(self.bo_asset.hostname, hostname)

    def test_return_report_when_user_not_assigned(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="test",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["return_report"],
        )
        with self.assertRaises(TransitionNotAllowedError):
            _check_instances_for_transition(
                instances=[self.bo_asset], transition=transition, requester=self.user_pl
            )

    def test_return_report_when_requester_is_not_assets_owner(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="test",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["must_be_owner_of_asset"],
        )
        with self.assertRaises(TransitionNotAllowedError):
            _check_instances_for_transition(
                instances=[self.bo_asset], transition=transition, requester=self.user_pl
            )

    @patch.object(ExternalService, "run")
    def test_a_report_is_generated(self, mock_method):
        GENERATED_FILE_CONTENT = REPORT_TEMPLATE = b"some-content"
        mock_method.return_value = GENERATED_FILE_CONTENT
        report_template = ReportTemplateFactory(template__data=REPORT_TEMPLATE)
        user = UserFactory()
        instances = [
            BackOfficeAssetFactory(
                user=UserFactory(first_name="James", last_name="Bond")
            )
        ]
        context = BackOfficeAsset._get_report_context(instances)
        attachment = generate_report(
            report_template.name,
            user,
            instances,
            report_template.language,
            context=context,
        )

        correct_filename = "{}_{}-{}_{}.pdf".format(
            timezone.now().isoformat()[:10],
            "james",
            "bond",
            report_template.report.name,
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment[0].original_filename, correct_filename)
        self.assertEqual(attachment[0].file.read(), GENERATED_FILE_CONTENT)

    @patch.object(ralph.back_office.models, "get_hook")
    def test_send_attachments_to_user_action_sends_email(self, mock_get_hook):
        mock_get_hook.return_value = lambda transition_name: EmailContext(
            from_email="foo@bar.pl", subject="sub", body="bod"
        )
        bo_asset = BackOfficeAssetFactory(model=self.model)
        _, transition, _ = self._create_transition(
            model=bo_asset,
            name="transition name",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["return_report"],
        )
        attachment = Attachment.objects.create(
            file=SimpleUploadedFile(
                "test_file.pdf", b"some content", content_type="application/pdf"
            ),
            uploaded_by=self.user_pl,
        )

        bo_asset.send_attachments_to_user(
            self.user_pl, transition.id, attachments=[attachment]
        )

        mock_get_hook.assert_called_once_with(
            "back_office.transition_action.email_context"
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "foo@bar.pl")

    def test_send_attachments_to_user_action_dont_send_email_without_attachments(self):  # noqa: E501
        bo_asset = BackOfficeAssetFactory(model=self.model)
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name="transition name",
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=["return_report"],
        )

        bo_asset.send_attachments_to_user(self.user_pl, transition.id)

        self.assertEqual(len(mail.outbox), 0)


class CheckerTestCase(SimpleTestCase):
    def test_requester_must_be_specified(self):
        errors = _check_assets_owner(instances=[], requester=None)
        self.assertTrue("__all__" in errors)


class BackOfficeAssetFormTest(TransitionTestCase, ClientMixin):
    def setUp(self):
        super().setUp()
        self.asset = BackOfficeAssetFactory()
        self.user = UserFactory()
        self.user.is_superuser = False
        self.user.is_staff = True
        self.passwd = "ralph"
        self.user.set_password(self.passwd)
        # Grant all permissions to the user
        permissions = Permission.objects.exclude(
            codename__in=[
                "view_backofficeasset_hostname_field",
                "view_backofficeasset_service_env_field",
                "change_backofficeasset_hostname_field",
                "change_backofficeasset_service_env_field",
            ]
        ).all()

        self.user.user_permissions.add(*permissions)
        self.user.regions.add(self.asset.region)
        self.user.save()
        self.login_as_user(user=self.user, password=self.passwd)
        self.data = {
            "hostname": self.asset.hostname,
            "model": self.asset.model.pk,
            "status": self.asset.status,
            "warehouse": self.asset.warehouse.pk,
            "region": self.asset.region.pk,
            "barcode": self.asset.barcode,
            "depreciation_rate": 0,
            "property_of": self.asset.property_of.id,
            "custom_fields-customfieldvalue-content_type-object_id-INITIAL_FORMS": "0",  # noqa: E501
            "custom_fields-customfieldvalue-content_type-object_id-MAX_NUM_FORMS": "1000",  # noqa: E501
            "custom_fields-customfieldvalue-content_type-object_id-MIN_NUM_FORMS": "0",  # noqa: E501
            "custom_fields-customfieldvalue-content_type-object_id-TOTAL_FORMS": "3",  # noqa: E501fhtml
        }

    def test_bo_admin_form_wo_access_to_service_env_and_hostname(self):
        url = reverse("admin:back_office_backofficeasset_change", args=(self.asset.pk,))
        resp = self.client.get(url, follow=True)

        self.assertEqual(resp.status_code, 200)

        self.assertIn("model", resp.context["adminform"].form.fields)
        self.assertNotIn("hostname", resp.context["adminform"].form.fields)
        self.assertNotIn("service_env", resp.context["adminform"].form.fields)

    @override_settings(BACKOFFICE_HOSTNAME_FIELD_READONLY=True)
    def test_bo_admin_form_with_readonly_hostname(self):
        self.assertTrue(self.login_as_user())
        asset = BackOfficeAssetFactory()

        url = reverse("admin:back_office_backofficeasset_change", args=(asset.pk,))
        resp = self.client.get(url, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("hostname", resp.context["adminform"].form.fields)
        self.assertTrue(
            resp.context["adminform"]
            .form.fields["hostname"]
            .widget.attrs.get("readonly")
        )

    def test_model_asset_type_back_office_shall_pass(self):
        back_office_model = DataCenterAssetModelFactory(
            type=ObjectModelType.from_name("back_office")
        )
        self.data.update({"model": back_office_model.pk})
        response = self.client.post(self.asset.get_absolute_url(), self.data)
        self.asset.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.asset.model, back_office_model)

    def test_model_asset_type_data_center_asset_shall_not_pass(self):
        back_office_model = DataCenterAssetModelFactory(
            type=ObjectModelType.from_name("data_center")
        )
        self.data.update({"model": back_office_model.pk})
        response = self.client.post(self.asset.get_absolute_url(), self.data)
        self.asset.refresh_from_db()
        self.assertIn("Model must be of", response.content.decode("utf-8"))
        self.assertNotEqual(self.asset.model, back_office_model)
        self.assertEqual(response.status_code, 200)
