from urllib.parse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context, Template


def _render_configuration(configuration, deployment, disable_reverse=False):
    def url(name, kwargs):
        if disable_reverse:
            return '{}({})'.format(
                name, ', '.join([str(value) for value in kwargs.values()])
            )
        return reverse(name, kwargs=kwargs)

    template = Template(configuration)
    ralph_instance = settings.RALPH_INSTANCE
    context = Context({
        'configuration_path': str(deployment.obj.configuration_path),
        'configuration_class_name': (
            deployment.obj.configuration_path.class_name if
            deployment.obj.configuration_path else None
        ),
        'configuration_module': (
            deployment.obj.configuration_path.module.name if
            deployment.obj.configuration_path else None
        ),
        'ralph_instance': ralph_instance,
        'deployment_id': deployment.id,
        'kickstart': urljoin(
            ralph_instance,
            url(
                'deployment_kickstart',
                kwargs={'deployment_id': deployment.id}
            ),
        ),
        'initrd': urljoin(
            ralph_instance,
            url(
                'deployment_files',
                kwargs={'deployment_id': deployment.id, 'file_type': 'initrd'}
            )
        ),
        'kernel': urljoin(
            ralph_instance,
            url(
                'deployment_files',
                kwargs={'deployment_id': deployment.id, 'file_type': 'kernel'}
            ),
        ),
        'dc': deployment.obj.rack.server_room.data_center.name,
        'domain': (
            deployment.obj.network_environment.domain
            if deployment.obj.network_environment else None
        ),
        'hostname': deployment.obj.hostname,
        'service_env': str(deployment.obj.service_env),
        'service_uid': (
            deployment.obj.service_env.service.uid if
            deployment.obj.service_env else None
        ),
        'done_url': urljoin(
            ralph_instance,
            url(
                'deployment_done',
                kwargs={'deployment_id': deployment.id}
            )
        ),
    })
    return template.render(context)
