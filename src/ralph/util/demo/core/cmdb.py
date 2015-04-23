# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util.demo import DemoData, register
from ralph.cmdb.models_ci import CIType

from ralph.cmdb.tests.utils import (
    CIRelationFactory,
    DeviceEnvironmentFactory,
    ServiceCatalogFactory,
)
from ralph.util.tests.utils import (
    BusinessLineFactory,
    ProfitCenterFactory,
)
from ralph.cmdb.models import CI_RELATION_TYPES


@register
class DemoDeviceEnvironment(DemoData):
    name = 'envs'
    title = 'Environments'

    def generate_data(self, data):
        # CITypes loaded from fixtures
        ci_type = CIType.objects.get(id=11)
        envs = [('prod', 'Prod'), ('test', 'Test'), ('dev', 'Dev')]
        return {
            slug: DeviceEnvironmentFactory(name=name, type=ci_type)
            for slug, name in envs
        }


@register
class DemoServices(DemoData):
    name = 'services'
    title = 'Services'

    def generate_data(self, data):
        # CITypes loaded from fixtures
        ci_type = CIType.objects.get(id=7)
        return {
            'backup_systems': ServiceCatalogFactory.create(
                type=ci_type,
                name='Backup systems',
                uid=10001,
            ),
            'load_balancing': ServiceCatalogFactory.create(
                type=ci_type,
                name='Load balancing',
                uid=10002,
            ),
            'databases': ServiceCatalogFactory.create(
                type=ci_type,
                name='Databases',
                uid=10003,
            ),
            'other': ServiceCatalogFactory.create(
                type=ci_type,
                uid=10004,
                name='Other',
            )
        }


@register
class DemoRelations(DemoData):
    name = 'relations'
    title = 'Relations'
    required = ['services', 'envs']

    def generate_data(self, data):
        for service in data['services'].values():
            for env in data['envs'].values():
                CIRelationFactory.create(
                    parent=service,
                    child=env,
                    type=CI_RELATION_TYPES.CONTAINS,
                )


@register
class DemoBusinessLine(DemoData):
    name = 'business_line'
    title = 'Business Line'
    required = ['services']

    def generate_data(self, data):
        business = BusinessLineFactory(name='IT')
        profit_center = ProfitCenterFactory(name='Default profit center')
        CIRelationFactory.create(
            parent=business,
            child=profit_center,
            type=CI_RELATION_TYPES.CONTAINS,
        )
        for service in data['services'].values():
            CIRelationFactory.create(
                parent=profit_center,
                child=service,
                type=CI_RELATION_TYPES.CONTAINS,
            )
