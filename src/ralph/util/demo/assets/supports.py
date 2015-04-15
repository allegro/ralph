# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util.demo import DemoData, register

from ralph_assets.tests.utils.supports import DCSupportFactory
from ralph_assets.tests.utils.licences import (
    LicenceFactory,
    LicenceAssetFactory,
)


@register
class DemoSupports(DemoData):
    name = 'assets_supports'
    title = 'Assets supports'
    required = ['assets_dc_assets']

    def generate_data(self, data):
        dc_support = DCSupportFactory()
        dc_support.assets.add(data['assets_dc_assets']['rack_server'])
        dc_support.assets.add(*data['assets_dc_assets']['blade_servers'])
        return {
            'dc_support': dc_support
        }


@register
class DemoLicences(DemoData):
    name = 'assets_licences'
    title = 'Assets licences'
    required = ['assets_dc_assets']

    def generate_data(self, data):
        [LicenceFactory() for _ in range(10)]
        licence = LicenceFactory()
        LicenceAssetFactory(
            licence=licence,
            asset=data['assets_dc_assets']['rack_server'],
        )
        return {
            'licence': licence,
        }
