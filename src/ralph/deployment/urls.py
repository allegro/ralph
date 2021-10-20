from django.conf.urls import url

from ralph.deployment.views import config, done_ping, files, ipxe

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
        r'^(?P<deployment_id>[-\w]+)/'
        r'('
        r'?P<config_type>kickstart|'
        r'preseed|'
        r'meta-data|'
        r'user-data|'
        r'script'
        r')$',
        config,
        name='deployment_config'
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
