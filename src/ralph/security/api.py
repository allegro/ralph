# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.security.models import SecurityScan, Vulnerability


class VulnerabilitySerializer(RalphAPISerializer):

    class Meta:
        model = Vulnerability
        depth = 1


class VulnerabilityViewSet(RalphAPIViewSet):
    queryset = Vulnerability.objects.all()
    serializer_class = VulnerabilitySerializer


class SecurityScanSerializer(RalphAPISerializer):
    vulnerabilities = VulnerabilitySerializer(many=True)

    class Meta:
        model = SecurityScan


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
