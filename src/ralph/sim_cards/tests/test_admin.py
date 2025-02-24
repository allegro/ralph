from django.urls import reverse

from ralph.back_office.models import BackOfficeAssetStatus
from ralph.back_office.tests.factories import WarehouseFactory
from ralph.sim_cards.models import SIMCard
from ralph.sim_cards.tests.factories import (
    CellularCarrierFactory,
    SIMCardFeatureFactory
)
from ralph.tests.base import RalphTestCase
from ralph.tests.factories import UserFactory
from ralph.tests.mixins import ClientMixin


class TestSIMCardForm(ClientMixin, RalphTestCase):
    def setUp(self):
        self.login_as_user()

    def test_create_correct_data(self):
        carrier = CellularCarrierFactory()

        warehouse = WarehouseFactory()

        user = UserFactory()
        owner = UserFactory()

        features = [SIMCardFeatureFactory() for _ in range(2)]
        expected_features_id = sorted(f.pk for f in features)

        sim_card_data = {
            "status": BackOfficeAssetStatus.new.id,
            "pin1": "1234",
            "pin2": "5678",
            "puk1": "12346",
            "puk2": "56786",
            "card_number": "1938462528298",
            "phone_number": "+4812345678911",
            "warehouse": warehouse.pk,
            "user": user.pk,
            "owner": owner.pk,
            "carrier": carrier.pk,
            "features": expected_features_id,
        }

        url = reverse("admin:sim_cards_simcard_add")

        response = self.client.post(url, sim_card_data, follow=True)
        self.assertNotIn("errors", response.context_data)

        sim_card_qs = SIMCard.objects.filter(card_number=sim_card_data["card_number"])
        self.assertTrue(sim_card_qs.exists())

        created_sim_card = sim_card_qs.first()
        assigned_features = sorted(f.pk for f in created_sim_card.features.all())

        self.assertEqual(expected_features_id, assigned_features)

    def test_create_incorrect_data(self):
        carrier = CellularCarrierFactory()

        warehouse = WarehouseFactory()

        user = UserFactory()

        owner = UserFactory()

        sim_card_data = {
            "status": BackOfficeAssetStatus.new,
            "pin1": "12343777448484",
            "pin2": "568fg458",
            "puk1": "123456789123456",
            "puk2": "567hdj8",
            "card_number": "1938462hdhd98",
            "phone_number": "481234568911",
            "warehouse": warehouse.pk,
            "user": user.pk,
            "owner": owner.pk,
            "carrier": carrier.pk,
        }
        url = reverse("admin:sim_cards_simcard_add")

        response = self.client.post(url, sim_card_data, follow=True)
        self.assertIn("errors", response.context_data)
        self.assertEqual(6, len(response.context_data["errors"]))
