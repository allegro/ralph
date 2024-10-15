from django.urls import reverse
from rest_framework import status

from ralph.api.tests._base import RalphAPITestCase
from ralph.ssl_certificates.models import SSLCertificate
from ralph.ssl_certificates.tests.factories import SSLCertificatesFactory


class SSLCertificatesAPITests(RalphAPITestCase):
    def setUp(self):
        super().setUp()
        self.certificate1: SSLCertificate
        self.certificate1, self.certificate2 = SSLCertificatesFactory.create_batch(2)

    def test_get_certificates_list(self):
        url = reverse("sslcertificate-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], SSLCertificate.objects.count())

    def test_get_certificate_with_details(self):
        url = reverse("sslcertificate-detail", args=(self.certificate1.id,))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for i in [
            "name",
            "domain_ssl",
            "date_from",
            "date_to",
            "san",
            "price",
            "certificate_repository",
        ]:
            self.assertEqual(response.data[i], getattr(self.certificate1, i))

    def test_get_ssl_with_service_env(self):
        url = reverse("sslcertificate-detail", args=(self.certificate1.id,))
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["service_env"]["id"], self.certificate1.service_env.id
        )
        self.assertEqual(
            response.data["service_env"]["service"],
            self.certificate1.service_env.service.name,
        )
        self.assertEqual(
            response.data["service_env"]["environment"],
            self.certificate1.service_env.environment.name,
        )
