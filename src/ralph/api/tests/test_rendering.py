from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ralph.api.tests._base import APIPermissionsTestMixin


class APIBrowsableClient(APIClient):
    renderer_classes_list = (
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
    default_format = 'text/html'


class RalphAPIRenderingTests(APIPermissionsTestMixin, APITestCase):
    client_class = APIBrowsableClient

    def test_rendering(self):
        url = reverse('test-ralph-api:api-root')
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
