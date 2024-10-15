from django.db import IntegrityError
from django.forms import ValidationError

from ralph.operations.models import OperationType
from ralph.operations.tests.factories import ChangeFactory, FailureFactory
from ralph.tests import RalphTestCase


class OperationModelsTestCase(RalphTestCase):
    fixtures = ["operation_types", "operation_statuses"]

    def setUp(self):
        self.failure = FailureFactory()

    def test_wrong_type(self):
        self.failure.type = OperationType.objects.get(name="Change")
        with self.assertRaises(
            ValidationError, msg="Invalid Operation type. Choose descendant of Failure"
        ):
            self.failure.clean()

    def test_ticket_id_unique(self):
        ticket_id = "FOO-42"
        ChangeFactory(ticket_id=ticket_id)

        with self.assertRaises(IntegrityError):
            ChangeFactory(ticket_id=ticket_id)
