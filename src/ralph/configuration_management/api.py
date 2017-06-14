import operator
from functools import reduce

from django.conf.urls import url
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.models import BaseObject
from ralph.configuration_management.models import SCMScan


class SCMScanSerializer(RalphAPISerializer):
    class Meta:
        model = SCMScan


class SCMScanSaveSerializer(RalphAPISaveSerializer):

    class Meta:
        fields = ('last_scan_date', 'scan_status')
        model = SCMScan


class SCMScanViewSet(RalphAPIViewSet):
    queryset = SCMScan.objects.all()
    serializer_class = SCMScanSerializer
    save_serializer_class = SCMScanSaveSerializer

    select_related = ['base_object']

    def get_baseobject(self, hostname):
        fields = [
            'asset__hostname',
            'cloudhost__hostname',
            'cluster__hostname',
            'virtualserver__hostname',
        ]

        queries = [
            Q(**{field: hostname.strip()})
            for field in fields
        ]

        return BaseObject.objects.filter(
            reduce(operator.or_, queries)
        ).distinct().first()

    def create(self, request, hostname):
        """Sets a SCM scan record for an object having matching hostname."""

        bo = self.get_baseobject(hostname)

        if bo is None:
            return Response(
                'No hostname matching {} found.'.format(hostname),
                status.HTTP_404_NOT_FOUND
            )

        serializer = self.save_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_data = {
            'last_scan_date': serializer.validated_data['last_scan_date'],
            'scan_status': serializer.validated_data['scan_status']
        }

        scan, created = SCMScan.objects.update_or_create(
            base_object_id=bo.id,
            defaults=update_data
        )

        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(self.serializer_class(scan).data, status=res_status)


router.register('scm-scan', SCMScanViewSet)
urlpatterns = [
    url(
            r'^scm-scan/(?P<hostname>[\w\.-]+)',
            SCMScanViewSet.as_view({'post': 'create'}),
            name='scm-scan-post'
    )
]
