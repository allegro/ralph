from ralph.api import RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.ssl_certificates.models import SSLCertificate


class SSLCertificateSerializer(BaseObjectSerializer):
    class Meta:
        model = SSLCertificate
        depth = 2
        exclude = ("content_type",)
        _skip_tags_field = True


class SSLCertificateViewSet(RalphAPIViewSet):
    queryset = SSLCertificate.objects.all()
    serializer_class = SSLCertificateSerializer
    filter_fields = [
        "name",
        "domain_ssl",
        "date_from",
        "date_to",
        "san",
        "price",
        "service_env__service__uid",
        "service_env__service__name",
        "service_env__service__id",
    ]
    select_related = ["service_env__service", "service_env__environment"]
    prefetch_related = ("licences__tags", "tags", "custom_fields", "content_type")


router.register(r"sslcertificates", SSLCertificateViewSet)
urlpatterns = []
