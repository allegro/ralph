# -*- coding: utf-8 -*-
from collections import OrderedDict

from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.data_center.models import DataCenterAsset
from ralph.networks.models.networks import IPAddress
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


class SaveSecurityScanSerializer(RalphAPISaveSerializer):

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
            base_object = None
            # first try to get base object by IPAddress
            # if not found, try by management ip
            # TODO: management_ip is temporary solution until it will be stored
            # properly in ipaddresses assigned to object
            try:
                ip_address = IPAddress.objects.get(address=host_ip)
            except IPAddress.DoesNotExist:
                pass
            else:
                base_object = ip_address.base_object_id
            if not base_object:
                try:
                    base_object = DataCenterAsset.objects.get(
                        management_ip=host_ip
                    ).baseobject_ptr_id
                except DataCenterAsset.DoesNotExist:
                    pass
            if not base_object:
                errors['host_ip'] = "IP is not assigned to any host"
        else:
            errors['host_ip'] = "Host IP is required"

        if errors:
            raise serializers.ValidationError(errors)
        data['base_object'] = base_object
        result = super(SaveSecurityScanSerializer, self).to_internal_value(data)
        return result


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer
    save_serializer_class = SaveSecurityScanSerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
