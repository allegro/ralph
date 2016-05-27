from django.conf.urls import url

from ralph.deployment.views import ipxe, kickstart

urlpatterns = [
    url(
        r'^ipxe/(?P<deployment_id>[-\w]+)$',
        ipxe,
        name='deployment_ipxe'
    ),
    url(
        r'^kickstart/(?P<deployment_id>[-\w]+)$',
        kickstart,
        name='deployment_kickstart'
    ),
]
