# -*- coding: utf-8 -*-
from dj.choices import Country
from django.conf import settings

from ralph.assets.country_utils import iso2_to_iso3, iso3_to_iso2
from ralph.assets.models import AssetLastHostname
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    CategoryFactory
)
from ralph.back_office.models import BackOfficeAsset
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.tests import RalphTestCase
from ralph.tests.factories import UserFactory


class HostnameGeneratorTests(RalphTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(username='hostname_2')
        cls.user_pl.country = Country.pl
        cls.user_pl.save()

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
            model=model, owner=self.user_pl, hostname=''
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
            model=model, owner=self.user_pl, hostname=''
        )
        BackOfficeAssetFactory(owner=self.user_pl, hostname='POLSW00003')
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
            model=model, owner=self.user_pl, hostname=''
        )
        self._check_hostname_not_generated(asset)

    def test_can_generate_hostname_for_model_with_hostname(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, owner=self.user_pl)
        self._check_hostname_is_generated(asset)

    def test_cant_generate_hostname_for_model_without_user(self):
        model = BackOfficeAssetModelFactory()
        asset = BackOfficeAssetFactory(model=model, owner=None, hostname='')
        self._check_hostname_not_generated(asset)

    def test_cant_generate_hostname_for_model_without_user_and_category(self):
        model = BackOfficeAssetModelFactory(category=None)
        asset = BackOfficeAssetFactory(model=model, owner=None, hostname='')
        self._check_hostname_not_generated(asset)

    def test_generate_next_hostname_out_of_range(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, owner=self.user_pl, hostname=''
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
