# -*- coding: utf-8 -*-
from rest_framework import serializers
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.security.models import SecurityScan, Vulnerability
from ralph.data_center.models.networks import IPAddress


#TODO:: sec-scan:info show all vulnarabilites-fix it
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
        result = super(SaveSecurityScanSerializer, self).to_internal_value(data)


        # host_ip 2 asset
        host_ip = data.get('host ip', None)
        if not host_ip:
            raise serializers.ValidationError("'Host ip' is required'")

        ip_address = IPAddress.objects.filter(address=host_ip)
        if ip_address.count() == 0:
            raise serializers.ValidationError("Unknown host ip")
        try:
            asset = ip_address.get().asset.datacenterasset
            if not asset:
                raise serializers.ValidationError(
                    "Ip is not assigned to any host"
                )
        except AttributeError:
            raise serializers.ValidationError("Ip is not assigned to any host")
        result['asset'] = asset


        # external_id to local_id
        converted = Vulnerability.objects.filter(external_vulnerability_id__in=data['external_vulnerabilities'])
        if len(converted) != len(data['external_vulnerabilities']):
            import ipdb; ipdb.set_trace()
            unknown = set(data['external_vulnerabilities']) - set([v.external_vulnerability_id for v in converted])
            raise serializers.ValidationError("Unknow external_vulnerability: {}".format(unknown))
        result['vulnerabilities'].extend(converted)


        return result


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer
    save_serializer_class = SaveSecurityScanSerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
