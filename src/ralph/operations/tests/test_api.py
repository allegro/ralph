from django.urls import reverse
from rest_framework import status

from ralph.accounts.tests.factories import UserFactory
from ralph.api.tests._base import RalphAPITestCase
from ralph.operations.models import Operation
from ralph.operations.tests.factories import OperationFactory


class OperationsAPITestCase(RalphAPITestCase):
    fixtures = ["operation_types", "operation_statuses"]

    def test_list_operations(self):
        num_operations = 10
        operation_title = "TEST OPERATION"
        operation_description = "TEST DESCRIPTION"

        for i in range(num_operations):
            OperationFactory(title=operation_title, description=operation_description)

        url = reverse("operation-list")
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], num_operations)

    def test_operation_details(self):
        op = OperationFactory()

        url = reverse("operation-detail", args=(op.id,))
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        received_op = response.data
        self.assertEqual(received_op["status"], op.status.name)
        self.assertEqual(received_op["title"], op.title)

    def test_operation_create(self):
        assignee = UserFactory()
        reporter = UserFactory()

        op_data = {
            "title": "deadbeef-title",
            "description": "deadbeef-description",
            "status": "Open",
            "type": "Change",
            "ticket_id": "DEADBEEF-42",
            "assignee": assignee.username,
            "reporter": reporter.username,
        }

        resp = self.client.post(
            reverse("operation-list"),
            data=op_data,
            format="json",
        )

        self.assertEqual(resp.status_code, 201)

        op = Operation.objects.get(ticket_id=op_data["ticket_id"])

        self.assertEqual(op_data["title"], op.title)
        self.assertEqual(op_data["description"], op.description)
        self.assertEqual(op_data["assignee"], op.assignee.username)
        self.assertEqual(op_data["reporter"], op.reporter.username)
        self.assertEqual(op_data["type"], op.type.name)
        self.assertEqual(op_data["status"], op.status.name)
