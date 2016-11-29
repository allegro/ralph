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
        r'^(?P<deployment_id>[-\w]+)/(?P<config_type>kickstart|preseed|script)$',  # noqa: E501
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
