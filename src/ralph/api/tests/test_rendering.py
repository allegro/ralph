import os
from importlib import import_module

from ddt import data, ddt
from django.db import connections
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from ralph.admin.tests.tests_views import FACTORY_MAP
from ralph.api.tests._base import APIPermissionsTestMixin
from ralph.tests.factories import UserFactory


class APIBrowsableClient(APIClient):
    renderer_classes_list = ("rest_framework.renderers.BrowsableAPIRenderer",)
    default_format = "text/html"


# If you want to test all items in the API, set BROWSE_ALL_API_ITEMS=1 env
BROWSE_ALL_API_ITEMS = os.environ.get("BROWSE_ALL_API_ITEMS", False)
DEFAULT_MAX_QUERIES = 20
# To get this just visit /api in your browser
ALL_API_ENDPOINTS = {
    "access-card": "/api/access-card/",
    "access-zone": "/api/access-zone/",
    "accessories": "/api/accessories/",
    "assetholders": "/api/assetholders/",
    "assetmodels": "/api/assetmodels/",
    "back-office-assets": "/api/back-office-assets/",
    "base-object-clusters": "/api/base-object-clusters/",
    # BaseObjectViewSet is a polymorphic viewset and in worst case it can generate many SQL queries
    # (some number per each different model) but not really N+1 for larger Ns.
    "base-objects": ("/api/base-objects/", 60),
    "base-objects-licences": "/api/base-objects-licences/",
    "base-objects-supports": "/api/base-objects-supports/",
    "budget-info": "/api/budget-info/",
    "business-segments": "/api/business-segments/",
    "categories": "/api/categories/",
    "cloud-flavors": "/api/cloud-flavors/",
    "cloud-hosts": "/api/cloud-hosts/",
    "cloud-images": "/api/cloud-images/",
    "cloud-projects": "/api/cloud-projects/",
    "cloud-providers": "/api/cloud-providers/",
    "cluster-types": "/api/cluster-types/",
    "clusters": "/api/clusters/",
    "configuration-classes": "/api/configuration-classes/",
    "configuration-modules": "/api/configuration-modules/",
    "custom-fields": "/api/custom-fields/",
    "data-center-assets": ("/api/data-center-assets/", 22),
    "data-centers": "/api/data-centers/",
    "databases": "/api/databases/",
    "dc-hosts": "/api/dc-hosts/",
    "disks": "/api/disks/",
    "dns-provider": "/api/dns-provider/",
    "dns-server-group": "/api/dns-server-group/",
    "dns-servers": "/api/dns-servers/",
    "domain-category": "/api/domain-category/",
    "domain-provider-additional-services": "/api/domain-provider-additional-services/",
    "domains": "/api/domains/",
    "environments": "/api/environments/",
    "ethernets": "/api/ethernets/",
    "fibre-channel-cards": "/api/fibre-channel-cards/",
    "graph": "/api/graph/",
    "groups": "/api/groups/",
    "ipaddresses": "/api/ipaddresses/",
    "licence-types": "/api/licence-types/",
    "licence-users": "/api/licence-users/",
    "licences": "/api/licences/",
    "manufacturer-kind": "/api/manufacturer-kind/",
    "manufacturers": "/api/manufacturers/",
    "memory": "/api/memory/",
    "network-environments": "/api/network-environments/",
    "network-kinds": "/api/network-kinds/",
    "networks": "/api/networks/",
    "office-infrastructures": "/api/office-infrastructures/",
    "operation": "/api/operation/",
    "operationstatus": "/api/operationstatus/",
    "operationtype": "/api/operationtype/",
    "processors": "/api/processors/",
    "profit-centers": "/api/profit-centers/",
    "rack-accessories": "/api/rack-accessories/",
    "racks": "/api/racks/",
    "regions": "/api/regions/",
    "scm-info": "/api/scm-info/",
    "security-scans": "/api/security-scans/",
    "server-rooms": "/api/server-rooms/",
    "services": "/api/services/",
    "services-environments": "/api/services-environments/",
    "sim-card": "/api/sim-card/",
    "sim-card-cellular-carrier": "/api/sim-card-cellular-carrier/",
    "sim-card-feature": "/api/sim-card-feature/",
    "software": "/api/software/",
    "sslcertificates": "/api/sslcertificates/",
    "support-types": "/api/support-types/",
    "supports": "/api/supports/",
    "teams": "/api/teams/",
    "transitions": "/api/transitions/",
    "transitions-action": "/api/transitions-action/",
    "transitions-history": "/api/transitions-history/",
    "transitions-job": "/api/transitions-job/",
    "transitions-model": "/api/transitions-model/",
    "users": "/api/users/",
    "vips": "/api/vips/",
    "virtual-server-types": "/api/virtual-server-types/",
    "virtual-servers": "/api/virtual-servers/",
    "vulnerabilities": "/api/vulnerabilities/",
    "warehouses": "/api/warehouses/",
}


@ddt
class RalphAPIRenderingTests(APIPermissionsTestMixin, APITestCase):
    client_class = APIBrowsableClient

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for factory in FACTORY_MAP.values():
            module_path, factory_class = factory.rsplit(".", 1)
            module = import_module(module_path)
            factory_model = getattr(module, factory_class)
            factory_model.create_batch(20)
        cls.user = UserFactory(is_staff=True, is_superuser=True)

    def test_rendering(self):
        url = reverse("test-ralph-api:api-root")
        self.client.force_authenticate(self.user1)
        response = self.client.get(url, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @data(*ALL_API_ENDPOINTS.keys())
    def test_browsable_endpoint(self, model_name):
        endpoint, max_queries = (
            ALL_API_ENDPOINTS[model_name]
            if isinstance(ALL_API_ENDPOINTS[model_name], tuple)
            else (ALL_API_ENDPOINTS[model_name], DEFAULT_MAX_QUERIES)
        )
        self.client.force_authenticate(self.user)
        with CaptureQueriesContext(connections["default"]) as cqc:
            response = self.client.get(endpoint, HTTP_ACCEPT="text/html")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(cqc.captured_queries), max_queries)

    @data(*ALL_API_ENDPOINTS.keys())
    def test_json_endpoint(self, model_name):
        endpoint, max_queries = (
            ALL_API_ENDPOINTS[model_name]
            if isinstance(ALL_API_ENDPOINTS[model_name], tuple)
            else (ALL_API_ENDPOINTS[model_name], DEFAULT_MAX_QUERIES)
        )
        self.client.force_authenticate(self.user)
        while True:
            with CaptureQueriesContext(connections["default"]) as cqc:
                response = self.client.get(endpoint, HTTP_ACCEPT="application/json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertGreater(len(response.json()["results"]), 0)
            self.assertLessEqual(
                len(cqc.captured_queries),
                max_queries,
                msg=f"Too many queries when getting {endpoint}."
                f"\nQueries count: {len(cqc.captured_queries)}."
                "\nQueries:\n"
                + "\n".join(query["sql"] for query in cqc.captured_queries),
            )
            endpoint = response.json()["next"]
            if not BROWSE_ALL_API_ITEMS or endpoint is None:
                break
