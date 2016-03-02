from django.forms import ValidationError

from ralph.operations.models import OperationType
from ralph.operations.tests.factories import FailureFactory
from ralph.tests import RalphTestCase


class OperationModelsTestCase(RalphTestCase):
    def setUp(self):
        self.failure = FailureFactory()

    def test_wrong_type(self):
        self.failure.type = OperationType.objects.get(name='Change')
        with self.assertRaises(
            ValidationError,
            msg='Invalid Operation type. Choose descendant of Failure'
        ):
            self.failure.clean()
