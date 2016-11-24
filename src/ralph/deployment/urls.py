from django.conf.urls import url

from ralph.deployment.views import done_ping, files, ipxe, kickstart

urlpatterns = [
    url(
        r'^boot.ipxe$',
        ipxe,
        name='deployment_ipxe'
    ),
    url(
        r'^(?P<deployment_id>[-\w]+)/boot.ipxe$',
        ipxe,
        name='deployment_ipxe'
    ),
    url(
        r'^(?P<deployment_id>[-\w]+)/kickstart$',
        kickstart,
        name='deployment_kickstart'
    ),
    url(
        r'^(?P<deployment_id>[-\w]+)/(?P<file_type>kernel|initrd|netboot)$',
        files,
        name='deployment_files'
    ),
    url(
        r'^(?P<deployment_id>[-\w]+)/mark_as_done$',
        done_ping,
        name='deployment_done'
    )
]
