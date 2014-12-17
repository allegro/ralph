# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json

from ralph.cmdb.models import CI, CI_STATE_TYPES
from ralph.cmdb.tests.utils import ServiceCatalogFactory
from ralph.discovery.tests.util import DeviceFactory
from ralph.ui.tests.global_utils import UserTestCase


class CMDBApiTest(UserTestCase):

    def test_change_service_state(self):
        """Change Service state from active to another state when Service have
        connected Devices"""
        data = json.dumps({'state': CI_STATE_TYPES.INACTIVE.id})
        service = ServiceCatalogFactory(state=CI_STATE_TYPES.ACTIVE.id)
        device = DeviceFactory(service=service)

        response = self.patch(
            '/api/v0.9/ci/{}/'.format(service.id),
            data,
            CONTENT_TYPE='application/json',
        )
        self.assertEqual(
            json.loads(response.content)['ci']['state'],
            'You can not change state because this service has linked devices.',
        )

        device.service = None
        device.save()

        response = self.patch(
            '/api/v0.9/ci/{}/'.format(service.id),
            data,
            CONTENT_TYPE='application/json',
        )
        chenged_service = CI.objects.get(id=service.id)
        self.assertEqual(chenged_service.state, CI_STATE_TYPES.INACTIVE.id)
