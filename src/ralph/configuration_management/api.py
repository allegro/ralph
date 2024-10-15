import operator
from functools import reduce

from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.assets.models import BaseObject
from ralph.configuration_management.models import SCMStatusCheck


class SCMInfoSerializer(RalphAPISerializer):
    class Meta:
        model = SCMStatusCheck
        fields = "__all__"


class SCMInfoSaveSerializer(RalphAPISaveSerializer):
    class Meta:
        fields = ("last_checked", "check_result")
        model = SCMStatusCheck


class SCMInfoViewSet(RalphAPIViewSet):
    queryset = SCMStatusCheck.objects.all()
    serializer_class = SCMInfoSerializer
    save_serializer_class = SCMInfoSaveSerializer

    select_related = ["base_object"]

    def get_baseobject(self, hostname):
        fields = [
            "asset__hostname",
            "cloudhost__hostname",
            "cluster__hostname",
            "virtualserver__hostname",
        ]

        queries = [Q(**{field: hostname.strip()}) for field in fields]

        return (
            BaseObject.objects.filter(reduce(operator.or_, queries)).distinct().first()
        )

    def delete(self, request, hostname):
        """Cleans up SCM scan record for an object having matching hostname."""

        bo = self.get_baseobject(hostname)

        if bo is None:
            return Response(
                "No hostname matching {} found.".format(hostname),
                status.HTTP_404_NOT_FOUND,
            )

        try:
            bo.scmstatuscheck.delete()
        except ObjectDoesNotExist:
            return Response(
                "SCM status is not set for the hostname {}".format(hostname),
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request, hostname):
        """Sets a SCM scan record for an object having matching hostname."""

        bo = self.get_baseobject(hostname)

        if bo is None:
            return Response(
                "No hostname matching {} found.".format(hostname),
                status.HTTP_404_NOT_FOUND,
            )

        serializer = self.save_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        update_data = {
            "last_checked": serializer.validated_data["last_checked"],
            "check_result": serializer.validated_data["check_result"],
        }

        scan, created = SCMStatusCheck.objects.update_or_create(
            base_object_id=bo.id, defaults=update_data
        )

        res_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK

        return Response(self.serializer_class(scan).data, status=res_status)


router.register("scm-info", SCMInfoViewSet)
urlpatterns = [
    url(
        r"^scm-info/(?P<hostname>[\w\.-]+)",
        SCMInfoViewSet.as_view({"post": "create", "delete": "delete"}),
        name="scm-info-post",
    )
]
