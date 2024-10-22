# -*- coding: utf-8 -*-
from collections import OrderedDict

import django_filters
from django.db import transaction
from rest_framework import serializers

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.networks.models.networks import IPAddress
from ralph.security.models import any_exceeded, SecurityScan, Vulnerability


class VulnerabilitySerializer(RalphAPISerializer):
    class Meta:
        model = Vulnerability
        depth = 1
        fields = "__all__"
        save_history = False


class VulnerabilityViewSet(RalphAPIViewSet):
    queryset = Vulnerability.objects.all().prefetch_related('tags')
    serializer_class = VulnerabilitySerializer
    filter_fields = [
        'external_vulnerability_id',
    ]


class SecurityScanSerializer(RalphAPISerializer):
    vulnerabilities = VulnerabilitySerializer(many=True)

    class Meta:
        model = SecurityScan
        fields = "__all__"


class SaveSecurityScanSerializer(RalphAPISaveSerializer):

    class Meta:
        model = SecurityScan
        fields = "__all__"
        save_history = False

    def to_internal_value(self, data):
        errors = OrderedDict()

        # external_id to local_id
        if 'external_vulnerabilities' in data:
            external_ids = set(data.get('external_vulnerabilities', []))
            converted = Vulnerability.objects.filter(
                external_vulnerability_id__in=external_ids)
            if len(converted) != len(external_ids):
                unknown = external_ids - set(
                    [str(v.external_vulnerability_id) for v in converted]
                )
                msg = "Unknow external_vulnerabilities: {}".format(
                    ', '.join(unknown)
                )
                errors['external_vulnerability'] = msg
            merged_vulnerabilities = data.get('vulnerabilities', [])
            merged_vulnerabilities.extend([c.id for c in converted])
            data['vulnerabilities'] = merged_vulnerabilities

        host_ip = data.get('host_ip', None)
        if host_ip:
            base_object = None
            # try to get base object by IPAddress
            try:
                ip_address = IPAddress.objects.get(address=host_ip)
            except IPAddress.DoesNotExist:
                pass
            else:
                base_object = ip_address.base_object
            if not base_object:
                errors['host_ip'] = "IP is not assigned to any host"
        else:
            errors['host_ip'] = "Host IP is required"

        if errors:
            raise serializers.ValidationError(errors)
        data['base_object'] = base_object.pk
        data['is_patched'] = not any_exceeded(
            Vulnerability.objects.filter(id__in=data['vulnerabilities'])
        )
        result = super().to_internal_value(data)
        return result


class IPFilter(django_filters.FilterSet):
    ip = django_filters.CharFilter(
        field_name='base_object__ethernet_set__ipaddress__address'
    )

    class Meta:
        model = IPAddress
        fields = ['ip']


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer
    save_serializer_class = SaveSecurityScanSerializer

    additional_filter_class = IPFilter
    prefetch_related = ("tags", "vulnerabilities__tags")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        ip = IPAddress.objects.filter(address=self.request.data.get(
            'host_ip', None)
        ).first()
        if ip:
            # one scan can exist for ip (because there are linked by onetoone)
            # so this removes old scan to allow updates by post
            SecurityScan.objects.filter(base_object=ip.base_object.id).delete()
        return super().create(request, *args, **kwargs)


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
