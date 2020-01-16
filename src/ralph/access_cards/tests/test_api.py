from datetime import datetime

from rest_framework import status
from rest_framework.reverse import reverse

from ralph.access_cards.tests.factories import AccessCardFactory
from ralph.accounts.tests.factories import RegionFactory
from ralph.api.tests._base import RalphAPITestCase
from ralph.tests.factories import UserFactory


class AccessCardTestCase(RalphAPITestCase):
    def assertAccessCardHasCertainFieldsAndValues(
        self, access_card, response_data
    ):
        self.assertEqual(response_data['status'], access_card.status.name)
        self.assertEqual(
            response_data['system_number'],
            access_card.system_number
        )
        self.assertEqual(
            response_data['visual_number'],
            access_card.visual_number
        )
        self.assertEqual(
            response_data['issue_date'],
            access_card.issue_date.strftime('%Y-%m-%d')
        )
        self.assertEqual(response_data['notes'], access_card.notes)
        self.assertEqual(
            response_data['user']['username'],
            access_card.user.username
        )
        self.assertEqual(
            response_data['owner']['username'],
            access_card.owner.username
        )
        self.assertEqual(
            response_data['region']['id'],
            access_card.region.id
        )

    def test_detail_access_card_returns_expected_fields(self):
        access_card = AccessCardFactory(
            issue_date=datetime.now(),
            user=UserFactory(),
            owner=UserFactory(),
            notes='test'
        )

        url = reverse('accesscard-detail', args=(access_card.id,))
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertAccessCardHasCertainFieldsAndValues(
            access_card, response.data
        )

    def test_list_access_card_returns_expected_fields(self):
        access_card1 = AccessCardFactory(
            issue_date=datetime.now(),
            user=UserFactory(),
            owner=UserFactory(),
            notes='test'
        )
        access_card2 = AccessCardFactory(
            issue_date=datetime.now(),
            user=UserFactory(),
            owner=UserFactory(),
            notes='test'
        )

        url = reverse('accesscard-list')
        response = self.client.get(url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertAccessCardHasCertainFieldsAndValues(
            access_card1, response.data['results'][0]
        )

        self.assertAccessCardHasCertainFieldsAndValues(
            access_card2, response.data['results'][1]
        )

    def test_class_access_card_test_case(self):
        region = RegionFactory()

        access_card = {
            'status': "in use",
            'visual_number': '654321',
            'system_number': 'F9876DSGV',
            'notes': 'test note',
            'issue_date': '2020-01-02',
            'region': region.id
        }
        url = reverse('accesscard-list')
        response = self.client.post(url, data=access_card)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        for field in access_card:
            self.assertEqual(response.data[field], access_card[field])
