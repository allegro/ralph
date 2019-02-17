from ralph.api import RalphAPIViewSet, router
from ralph.api.serializers import RalphAPISaveSerializer
from ralph.ssl_certificates.models import SSLCertificate

from ralph.assets.api.serializers import (
    BaseObjectSerializer,
)


class SSLCertificateSerializer(BaseObjectSerializer):

    class Meta:
        model = SSLCertificate
        depth = 2
        exclude = ("content_type", )
        _skip_tags_field = True


class SSLCertificateViewSet(RalphAPIViewSet):
    queryset = SSLCertificate.objects.all()
    serializer_class = SSLCertificateSerializer
    filter_fields = [
        "name", "domain_ssl", "date_from", "date_to", "san", "price",
        'service_env__service__uid',
        'service_env__service__name',
        'service_env__service__id',
    ]
    select_related = [
        'service_env__service', 'service_env__environment'
    ]

class SaveSSLCertificate(RalphAPISaveSerializer):

    class Meta:
        model = SSLCertificate


router.register(r'sslcertificates', SSLCertificateViewSet)
urlpatterns = []
