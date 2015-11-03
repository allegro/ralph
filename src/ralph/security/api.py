# -*- coding: utf-8 -*-
#from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
#from ralph.supports.models import Support, SupportType
#
#
#class SupportTypeSerializer(RalphAPISerializer):
#    class Meta:
#        model = SupportType
#
#
#class SupportTypeViewSet(RalphAPIViewSet):
#    queryset = SupportType.objects.all()
#    serializer_class = SupportTypeSerializer
#
#
#class SupportSerializer(RalphAPISerializer):
#    class Meta:
#        model = Support
#        depth = 1
#        # temporary - waiting for Polymorphic
#        # (https://github.com/allegro/ralph/pull/1725)
#        # we should create serializer for this field which will call
#        # proper serializer for each type returned by Polymorphic or try to
#        # use generic nested serializer for concrete type
#        exclude = ('base_objects',)
#
#
#class SupportViewSet(RalphAPIViewSet):
#    queryset = Support.objects.all()
#    serializer_class = SupportSerializer
#
#
#router.register(r'supports', SupportViewSet)
#router.register(r'support-types', SupportTypeViewSet)
#urlpatterns = []




from ralph.api import RalphAPISerializer, RalphAPIViewSet, router
from ralph.security.models import SecurityScan, Vulnerability


class SecurityScanSerializer(RalphAPISerializer):
    class Meta:
        model = SecurityScan


class SecurityScanViewSet(RalphAPIViewSet):
    queryset = SecurityScan.objects.all()
    serializer_class = SecurityScanSerializer


class VulnerabilitySerializer(RalphAPISerializer):

    class Meta:
        model = Vulnerability
        #TODO:: rm it
        #exclude = ('security_scans', )
        depth = 1



class VulnerabilityViewSet(RalphAPIViewSet):
    queryset = Vulnerability.objects.all()
    serializer_class = VulnerabilitySerializer


router.register(r'vulnerabilities', VulnerabilityViewSet)
router.register(r'security-scans', SecurityScanViewSet)
urlpatterns = []
