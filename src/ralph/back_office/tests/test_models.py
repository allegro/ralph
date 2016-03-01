# -*- coding: utf-8 -*-
from datetime import datetime
from unittest.mock import patch

from dj.choices import Country
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory
from django.utils import timezone

from ralph.accounts.tests.factories import RegionFactory
from ralph.assets.country_utils import iso2_to_iso3, iso3_to_iso2
from ralph.assets.models import AssetLastHostname
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    CategoryFactory,
    DataCenterAssetModelFactory,
    ServiceEnvironmentFactory
)
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import RackFactory
from ralph.lib.external_services import ExternalService
from ralph.lib.transitions.models import (
    _check_instances_for_transition,
    run_field_transition,
    TransitionNotAllowedError
)
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.licences.tests.factories import LicenceFactory
from ralph.reports.factories import ReportTemplateFactory
from ralph.tests import RalphTestCase
from ralph.tests.factories import UserFactory


class HostnameGeneratorTests(RalphTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region_pl = RegionFactory(name='PL', country=Country.pl)
        cls.region_pl.country = Country.pl
        cls.region_pl.save()

    def _check_hostname_not_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertEqual(changed_asset.hostname, '')

    def _check_hostname_is_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertTrue(len(changed_asset.hostname) > 0)

    def test_generate_first_hostname(self):
        """Scenario:
         - none of assets has hostname
         - after generate first of asset have XXXYY00001 in hostname field
        """
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, hostname=''
        )
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC00001')

    def test_generate_next_hostname(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, region=self.region_pl, hostname=''
        )
        BackOfficeAssetFactory(region=self.region_pl, hostname='POLSW00003')
        AssetLastHostname.increment_hostname(prefix='POLPC')
        AssetLastHostname.increment_hostname(prefix='POLPC')
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC00003')

    def test_cant_generate_hostname_for_model_without_category(self):
        model = BackOfficeAssetModelFactory(category=None)
        asset = BackOfficeAssetFactory(
            model=model, region=self.region_pl, hostname=''
        )
        self._check_hostname_not_generated(asset)

    def test_can_generate_hostname_for_model_with_hostname(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, region=self.region_pl)
        self._check_hostname_is_generated(asset)

    def test_generate_next_hostname_out_of_range(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, region=self.region_pl, hostname=''
        )
        AssetLastHostname.objects.create(
            prefix='POLPC', counter=99999
        )
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC100000')

    def test_convert_iso2_to_iso3(self):
        self.assertEqual(iso2_to_iso3('PL'), 'POL')

    def test_convert_iso3_to_iso2(self):
        self.assertEqual(iso3_to_iso2('POL'), 'PL')

    def test_validate_imei(self):
        bo_asset_failed = BackOfficeAssetFactory(imei='failed')
        bo_asset = BackOfficeAssetFactory(imei='990000862471854')

        self.assertFalse(bo_asset_failed.validate_imei())
        self.assertTrue(bo_asset.validate_imei())


class TestBackOfficeAsset(RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.region_pl = RegionFactory(name='PL', country=Country.pl)
        cls.region_us = RegionFactory(name='US', country=Country.us)
        cls.category = CategoryFactory(code='PC')
        cls.category_without_code = CategoryFactory()
        cls.model = BackOfficeAssetModelFactory(category=cls.category)
        cls.model_without_code = BackOfficeAssetModelFactory(
            category=cls.category_without_code
        )

    def setUp(self):
        super().setUp()
        AssetLastHostname.objects.create(prefix='POLPC', counter=1000)
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc',
            region=self.region_pl,
        )
        self.bo_asset_2 = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc2',
            region=self.region_pl,
            status=BackOfficeAssetStatus.liquidated.id,
            invoice_date=None
        )
        self.bo_asset_3 = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc3',
            region=self.region_pl,
            status=BackOfficeAssetStatus.liquidated.id,
            invoice_date=datetime(2016, 1, 11).date(),
            depreciation_rate=50
        )
        self.bo_asset_4 = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc3',
            region=self.region_pl,
            status=BackOfficeAssetStatus.liquidated.id,
            invoice_date=datetime(2016, 1, 11).date(),
            depreciation_end_date=datetime(2015, 1, 11).date(),
            depreciation_rate=50
        )
        self.category_parent = CategoryFactory(
            code='Mob1', default_depreciation_rate=30
        )
        self.category_2 = CategoryFactory(
            code='Mob2', default_depreciation_rate=25
        )
        self.category_3 = CategoryFactory(
            code='Mob3', parent=self.category_parent,
            default_depreciation_rate=0
        )

    def test_try_assign_hostname(self):
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_no_change(self):
        self.bo_asset.hostname = 'POLPC01001'
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_no_hostname(self):
        self.bo_asset.hostname = ''
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_forced(self):
        self.bo_asset.hostname = 'POLPC001010'
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_with_country(self):
        self.bo_asset._try_assign_hostname(country='US', commit=True)
        self.assertEqual(self.bo_asset.hostname, 'USPC00001')

    def test_try_assign_hostname_category_without_code(self):
        bo_asset_2 = BackOfficeAssetFactory(
            model=self.model_without_code, hostname='abcd'
        )
        bo_asset_2._try_assign_hostname(commit=True)
        self.assertEqual(bo_asset_2.hostname, 'abcd')

    def test_try_assign_hostname_when_status_in_progress(self):
        self.bo_asset.status = BackOfficeAssetStatus.new
        self.bo_asset.save()

        self.bo_asset.status = BackOfficeAssetStatus.in_progress
        self.bo_asset.save()
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_get_autocomplete_queryset(self):
        queryset = BackOfficeAsset.get_autocomplete_queryset()
        self.assertEquals(1, queryset.count())

    def test_buyout_date(self):
        self.assertEqual(
            self.bo_asset_3.buyout_date,
            datetime(2018, 2, 11).date()
        )

        self.assertEqual(
            self.bo_asset_2.buyout_date,
            None
        )

    def test_butout_date_with_depreciation_end_date(self):
        self.assertEqual(
            self.bo_asset_4.buyout_date,
            datetime(2015, 1, 11).date()
        )

    def test_get_depreciation_rate(self):
        self.assertEqual(self.category_2.get_default_depreciation_rate(), 25)
        self.assertEqual(self.category_3.get_default_depreciation_rate(), 30)

class TestBackOfficeAssetTransitions(TransitionTestCase, RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(country=Country.pl)
        cls.region_pl = RegionFactory(name='PL', country=Country.pl)
        cls.region_us = RegionFactory(name='US', country=Country.us)
        cls.region_us_2 = RegionFactory(name='US', country=Country.us)
        cls.category = CategoryFactory(code='PC')
        cls.model = BackOfficeAssetModelFactory(category=cls.category)

    def setUp(self):
        super().setUp()
        AssetLastHostname.objects.create(prefix='POLPC', counter=1000)
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc',
            region=self.region_us,
        )
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.request = RequestFactory().get('/assets/')
        self.request.user = self.user_pl
        # ugly hack from https://code.djangoproject.com/ticket/17971
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def test_convert_to_data_center_asset(self):
        bo_asset = BackOfficeAssetFactory()
        bo_asset_pk = bo_asset.pk
        hostname = bo_asset.hostname
        rack = RackFactory()
        BackOfficeAsset.convert_to_data_center_asset(
            instances=[bo_asset],
            rack=rack.id,
            service_env=ServiceEnvironmentFactory().id,
            position=1,
            model=DataCenterAssetModelFactory().id,
            request=None
        )
        dc_asset = DataCenterAsset.objects.get(pk=bo_asset_pk)
        self.assertEqual(dc_asset.rack.id, rack.id)
        self.assertFalse(
            BackOfficeAsset.objects.filter(pk=bo_asset_pk).exists()
        )
        self.assertEqual(dc_asset.hostname, hostname)

    def test_assign_many_licences(self):
        asset = BackOfficeAssetFactory()
        licences = [LicenceFactory() for i in range(2)]
        self.assertFalse(asset.licences.all())

        BackOfficeAsset.assign_licence(
            instances=[asset], request=None, licences=licences,
        )

        self.assertCountEqual(
            [base_obj_lic.licence.id for base_obj_lic in asset.licences.all()],
            [licence.id for licence in licences],
        )

    def test_change_hostname(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['change_hostname']
        )
        run_field_transition(
            [self.bo_asset],
            field='status',
            transition_obj_or_name=transition,
            data={'change_hostname__country': Country.pl},
            request=self.request
        )
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_assign_owner(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['assign_owner']
        )
        run_field_transition(
            [self.bo_asset],
            field='status',
            transition_obj_or_name=transition,
            data={'assign_owner__owner': self.user_pl.id},
            request=self.request
        )

    def try_change_status_to_in_progress_during_transition(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.in_progress.id,
            actions=['assign_owner']
        )
        self.bo_asset.run_status_transition(
            transition_obj_or_name=transition,
            data={'assign_owner__owner': self.user_pl.id},
            request=self.request
        )
        self.assertEqual(self.bo_asset.hostname, 'USPC01001')

    def test_return_report_when_user_not_assigned(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['return_report']
        )
        with self.assertRaises(TransitionNotAllowedError):
            _check_instances_for_transition([self.bo_asset], transition)

    @patch.object(ExternalService, "run")
    def test_report_is_generated(self, mock_method):
        GENERATED_FILE_CONTENT = REPORT_TEMPLATE = b'some-content'
        mock_method.return_value = GENERATED_FILE_CONTENT
        report_template = ReportTemplateFactory(template__data=REPORT_TEMPLATE)
        request = RequestFactory().get('/')  # only request's user is important
        request.user = UserFactory()
        instances = [
            BackOfficeAssetFactory(
                user=UserFactory(first_name="James", last_name="Bond")
            )
        ]

        attachment = BackOfficeAsset._generate_report(
            report_template.name, request, instances, report_template.language)

        correct_filename = '{}_{}-{}_{}.pdf'.format(
            timezone.now().isoformat()[:10], 'james', 'bond',
            report_template.report.name,
        )
        self.assertEqual(attachment.original_filename, correct_filename)
        self.assertEqual(attachment.file.read(), GENERATED_FILE_CONTENT)
