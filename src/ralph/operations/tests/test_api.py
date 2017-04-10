from django.core.urlresolvers import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.operations.tests.factories import OperationFactory


class OperationsAPITestCase(RalphAPITestCase):
    fixtures = ['operation_types', 'operation_statuses']

    def test_list_operations(self):
        num_operations = 10
        operation_title = 'TEST OPERATION'
        operation_description = 'TEST DESCRIPTION'

        for i in range(num_operations):
            OperationFactory(
                title=operation_title,
                description=operation_description
            )

        url = reverse('operation-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], num_operations)

    def test_operation_details(self):
        op = OperationFactory()

        url = reverse('operation-detail', args=(op.id,))
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        received_op = response.data
        self.assertEqual(received_op['status']['name'], op.status.name)
        self.assertEqual(received_op['title'], op.title)
