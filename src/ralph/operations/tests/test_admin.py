from django.test import TestCase
from django.urls import reverse

from ralph.operations.tests.factories import OperationFactory
from ralph.tests.mixins import ClientMixin


class OperationAdminViewTest(ClientMixin, TestCase):
    def test_operation_changelist_should_run_2_queries(self):
        OperationFactory.create_batch(5)
        with self.assertNumQueries(2):
            self.client.get(
                reverse("admin:operations_operation_changelist"),
            )
