# -*- coding: utf-8 -*-
from django.core import mail

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import (
    ServiceEnvironmentFactory,
    ServiceFactory
)
from ralph.data_center.tests.factories import DataCenterAssetFactory
from ralph.tests import RalphTestCase


class NotificationTest(RalphTestCase):

    def test_notificaiton_change_service_in_datacenterasset(self):
        old_service = ServiceFactory(name='test')
        new_service = ServiceFactory(name='prod')
        old_service.business_owners.add(UserFactory(email='test1@test.pl'))
        new_service.business_owners.add(UserFactory(email='test2@test.pl'))
        self.dca = DataCenterAssetFactory(
            service_env=ServiceEnvironmentFactory(
                service=old_service
            )
        )
        self.dca.service_env = ServiceEnvironmentFactory(
            service=new_service
        )
        self.dca._handle_post_save = True
        self.dca.save()

        self.assertEqual(
            'Device has been assigned to Service: {} ({})'.format(
                new_service, self.dca
            ),
            mail.outbox[0].subject
        )
        self.assertCountEqual(
            mail.outbox[0].to,
            ['test1@test.pl', 'test2@test.pl']
        )
