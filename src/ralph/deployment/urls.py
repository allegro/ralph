from django.conf.urls import url

from ralph.deployment.views import ipxe

urlpatterns = [
    url(
        r'^ipxe/?$',
        ipxe,
        name='deployment_ipxe'
    ),
]
