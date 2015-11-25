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
        # external_id to local_id

        from collections import OrderedDict
        errors = OrderedDict()
        #errors['vulnerabilities'] = 'msg'
        #raise serializers.ValidationError(errors)

        if 'external_vulnerabilities' in data:
            external_ids = data.getlist('external_vulnerabilities')
            converted = Vulnerability.objects.filter(external_vulnerability_id__in=external_ids)
            if len(converted) != len(external_ids):
                unknown = set(external_ids) - set(
                    [str(v.external_vulnerability_id) for v in converted]
                )
                msg = "Unknow external_vulnerabilities: {}".format(
                    ', '.join(unknown)
                )
                errors['external_vulnerability'] = msg
                #raise serializers.ValidationError("Unknow external_vulnerability: {}".format(unknown))
            merged_vulnerabilities = data.getlist('vulnerabilities') or []
            merged_vulnerabilities.extend([c.id for c in converted])
            data.setlist('vulnerabilities', merged_vulnerabilities)

        # host_ip 2 asset
        host_ip = data.get('host ip', None)
        if not host_ip:
            errors['host_ip'] = "'Host ip' is required'"
            #raise serializers.ValidationError("'Host ip' is required'")

        ip_address = IPAddress.objects.filter(address=host_ip)
        if ip_address.count() == 0:
            errors['host_ip'] = "Unknown host ip"
            #raise serializers.ValidationError("Unknown host ip")
        try:
            #asset = ip_address.get().asset.datacenterasset
            asset = ip_address[0].base_object and ip_address[0].base_object.asset
            if not asset:
                errors['host_ip'] = "Ip is not assigned to any host"
                #raise serializers.ValidationError(
                #    "Ip is not assigned to any host"
                #)
        except AttributeError:
            errors['host_ip'] = "Ip is not assigned to any host"
            #raise serializers.ValidationError("Ip is not assigned to any host")

        if errors:
            raise serializers.ValidationError(errors)

        result = super(SaveSecurityScanSerializer, self).to_internal_value(data)
        result['asset'] = asset
        return result


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer
    save_serializer_class = SaveSecurityScanSerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
