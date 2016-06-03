import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import Context, Template

from ralph.admin.helpers import get_client_ip
from ralph.deployment.models import Deployment

logger = logging.getLogger(__name__)


def _get_preboot(deployment_id):
    preboot = None
    try:
        preboot = Deployment.objects.get(id=deployment_id).preboot
    except ValueError:
        logger.warning('Incorrect UUID: {}'.format(deployment_id))
        raise SuspiciousOperation('Malformed UUID')
    except Deployment.DoesNotExist:
        logger.warning('Deployment with UUID: {} doesn\'t exist' .format(
            deployment_id
        ))
        raise Http404
    return preboot


def _render_configuration(configuration, deployment):
    template = Template(configuration)
    ralph_instance = settings.RALPH_INSTANCE
    context = Context({
        'ralph_instance': ralph_instance,
        'deployment_id': deployment.id,
        'kickstart': ralph_instance + reverse('deployment_kickstart', kwargs={
            'deployment_id': deployment.id,
        }),
        'initrd': ralph_instance + reverse('deployment_files', kwargs={
            'deployment_id': deployment.id,
            'file_type': 'initrd'
        }),
        'kernel': ralph_instance + reverse('deployment_files', kwargs={
            'deployment_id': deployment.id,
            'file_type': 'kernel'
        }),
        'dc': deployment.obj.rack.server_room.data_center,
        'done_url': ralph_instance + reverse('deployment_done', kwargs={
            'deployment_id': deployment.id,
        })
    })
    return template.render(context)


def ipxe(request, deployment_id=None):
    """View returns boot's config for iPXE depends on client IP.

    Args:
        request (object): standard Django's object for request.

    Returns:
        HttpResponse: contains config for iPXE

    Raises:
        Http404: if deployment with specified UUID doesn't exist
    """
    ip = get_client_ip(request)
    try:
        if deployment_id:
            deployment = Deployment.objects.get(id=deployment_id)
        else:
            deployment = Deployment.get_deployment_for_ip(ip)
    except Deployment.DoesNotExist:
        raise Http404
    configuration = _render_configuration(
        deployment.preboot.get_configuration('ipxe'), deployment
    )
    return HttpResponse(configuration, content_type='text/plain')


def kickstart(request, deployment_id):
    """View returns rendered kickstart configuration.

    Args:
        deployment_id (string): deployment's UUID

    Returns:
        HttpResponse: rendered kickstart

    Raises:
        Http404: if deployment with specified UUID doesn't exist
    """
    preboot = _get_preboot(deployment_id)
    configuration = preboot.get_configuration('kickstart')
    if configuration is None:
        raise Http404
    configuration = _render_configuration(
        configuration, Deployment.objects.get(id=deployment_id)
    )
    return HttpResponse(
        configuration.replace('\r\n', '\n').replace('\r', '\n'),
        content_type='text/plain'
    )


def files(request, file_type, deployment_id):
    """Redirect client to server with static.

    Args:
        file_type (choices): kernel|initrd - type of file
        deployment_id (string): deployment's UUID

    Returns:
        HttpResponse: redirect to file on static server

    Raises:
        Http404: if deployment with specified UUID doesn't exist

    """
    preboot = _get_preboot(deployment_id)
    file_url = preboot.get_file_url(file_type)
    if file_url is None:
        raise Http404
    return HttpResponseRedirect(file_url)


def done_ping(request, deployment_id):
    """View mark specified deployment (by UUID from URL) as finished.

    Args:
        deployment_id (string): deployment's UUID

    Returns:
        HttpResponse: document with 'marked' sentence
    """
    ip = get_client_ip(request)
    Deployment.mark_as_done(deployment_id)
    logger.info(
        'Deployment {} for {} marked as done.'.format(
            deployment_id, ip
        )
    )
    return HttpResponse('marked', content_type='text/plain')
