# -*- coding: utf-8 -*-
from django.core import mail
from django.db import transaction
from django.test import TransactionTestCase

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.tests.factories import (
    ServiceEnvironmentFactory,
    ServiceFactory
)
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import DataCenterAssetFactory


class NotificationTest(TransactionTestCase):
    def test_if_notification_is_send_when_data_center_asset_is_saved(self):
        old_service = ServiceFactory(name="test")
        new_service = ServiceFactory(name="prod")
        old_service.business_owners.add(UserFactory(email="test1@test.pl"))
        new_service.business_owners.add(UserFactory(email="test2@test.pl"))
        self.dca = DataCenterAssetFactory(
            service_env=ServiceEnvironmentFactory(service=old_service)
        )

        # fetch DCA to start with clean state in post_commit signals
        # (ex. invalidate call to notification handler during creating of DCA)
        self.dca = DataCenterAsset.objects.get(pk=self.dca.pk)
        self.dca.service_env = ServiceEnvironmentFactory(service=new_service)
        with transaction.atomic():
            self.dca.save()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            "Device has been assigned to Service: {} ({})".format(
                new_service, self.dca
            ),
            mail.outbox[0].subject,
        )
        self.assertCountEqual(mail.outbox[0].to, ["test1@test.pl", "test2@test.pl"])
