from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.test import TransactionTestCase


class RalphAdminTestCase(TransactionTestCase):
    def setUp(self):
        try:
            self.user = get_user_model().objects.get(username="root")
        except get_user_model().DoesNotExist:
            self.user = get_user_model().objects.create_superuser(
                username="root", password="password", email="email@email.pl"
            )
        result = self.client.login(username="root", password="password")
        self.assertEqual(result, True)

    def get_response_queryset(self, url) -> QuerySet:
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.context["cl"].queryset
