# -*- coding: utf-8 -*-
from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.assets.api.serializers import BaseObjectSerializer
from ralph.virtual.models import CloudFlavor, CloudHost, CloudProject


class CloudFlavorSerializer(RalphAPISerializer):
    class Meta:
        model = CloudFlavor
        exclude = ['content_type']

class CloudFlavorViewSet(RalphAPIViewSet):
    queryset = CloudFlavor.objects.all()
    serializer_class = CloudFlavorSerializer


class CloudHostSerializer(RalphAPISerializer):
    class Meta:
        model = CloudHost
        exclude = ['content_type', 'cloudflavor']


class CloudHostViewSet(RalphAPIViewSet):
    queryset = CloudHost.objects.all()
    serializer_class = CloudHostSerializer


class CloudProjectSerializer(BaseObjectSerializer):
    class Meta:
        model = CloudProject
        depth = 1
        exclude = ['content_type', 'cloudprovider']


class CloudProjectViewSet(RalphAPIViewSet):
    queryset = CloudProject.objects.all()
    serializer_class = CloudProjectSerializer

router.register(r'cloud-flavors', CloudFlavorViewSet)
router.register(r'cloud-hosts', CloudHostViewSet)
router.register(r'cloud-projects', CloudProjectViewSet)
urlpatterns = []
