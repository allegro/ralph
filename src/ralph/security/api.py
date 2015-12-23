# -*- coding: utf-8 -*-
from collections import OrderedDict

from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.data_center.models.networks import IPAddress
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


class SaveSecurityScanSerializer(RalphAPISerializer):

    class Meta:
        model = SecurityScan

    def to_internal_value(self, data):
        errors = OrderedDict()

        # external_id to local_id
        if 'external_vulnerabilities' in data:
            external_ids = data.getlist('external_vulnerabilities')
            converted = Vulnerability.objects.filter(
                external_vulnerability_id__in=external_ids)
            if len(converted) != len(external_ids):
                unknown = set(external_ids) - set(
                    [str(v.external_vulnerability_id) for v in converted]
                )
                msg = "Unknow external_vulnerabilities: {}".format(
                    ', '.join(unknown)
                )
                errors['external_vulnerability'] = msg
            merged_vulnerabilities = data.getlist('vulnerabilities') or []
            merged_vulnerabilities.extend([c.id for c in converted])
            data.setlist('vulnerabilities', merged_vulnerabilities)

        host_ip = data.get('host_ip', None)
        if host_ip:
            ip_address = IPAddress.objects.filter(address=host_ip)
            if ip_address.count() == 0:
                errors['host_ip'] = "Unknown host IP"
            msg = "IP is not assigned to any host"
            try:
                base_object = ip_address[0].base_object
                if not base_object:
                    errors['host_ip'] = msg
            except AttributeError:
                errors['host_ip'] = msg
        else:
            errors['host_ip'] = "'Host IP is required'"

        if errors:
            raise serializers.ValidationError(errors)
        data['base_object'] = ip_address[0].base_object.id
        result = super(SaveSecurityScanSerializer, self).to_internal_value(data)
        result['base_object'] = base_object
        return result


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer
    save_serializer_class = SaveSecurityScanSerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
