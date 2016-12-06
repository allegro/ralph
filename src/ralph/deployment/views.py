import logging
from django.core.exceptions import SuspiciousOperation
from django.http import Http404, HttpResponse, HttpResponseRedirect

from ralph.admin.helpers import get_client_ip
from ralph.assets.models import Ethernet
from ralph.deployment.models import Deployment
from ralph.deployment.utils import _render_configuration

logger = logging.getLogger(__name__)


DEPLOYMENT_404_MSG = 'Deployment {} doesn\'t exist'


def get_object_or_404_with_message(model, msg, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        logger.error(msg)
        raise Http404(msg)


def _get_preboot(deployment_id):
    error_msg = 'Deployment with UUID: {} doesn\'t exist' .format(
        deployment_id
    )
    try:
        return get_object_or_404_with_message(
            model=Deployment,
            msg=error_msg,
            id=deployment_id
        ).preboot
    except ValueError:
        logger.warning('Incorrect UUID: {}'.format(deployment_id))
        raise SuspiciousOperation('Malformed UUID')


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
    except Ethernet.DoesNotExist:
        logger.warning('Deployment does not exists for ip: {}'.format(ip))
        raise Http404
    except Deployment.DoesNotExist:
        logger.warning(DEPLOYMENT_404_MSG.format(deployment_id))
        raise Http404
    configuration = _render_configuration(
        deployment.preboot.get_configuration('ipxe'), deployment
    )
    return HttpResponse(configuration, content_type='text/plain')


def config(request, deployment_id, config_type):
    """View returns rendered config configuration.

    Args:
        deployment_id (string): deployment's UUID
        config_type (choices): kickstart|preseed|script - type of config

    Returns:
        HttpResponse: rendered config

    Raises:
        Http404: if deployment with specified UUID doesn't exist
    """
    preboot = _get_preboot(deployment_id)
    configuration = preboot.get_configuration(config_type)
    if configuration is None:
        logger.warning('{} for deployment {} doesn\'t exist'.format(
            config_type, deployment_id
        ))
        raise Http404
    deployment = get_object_or_404_with_message(
        model=Deployment,
        msg=DEPLOYMENT_404_MSG.format(deployment_id),
        id=deployment_id
    )
    configuration = _render_configuration(configuration, deployment)
    return HttpResponse(
        configuration.replace('\r\n', '\n').replace('\r', '\n'),
        content_type='text/plain'
    )


def files(request, file_type, deployment_id):
    """Redirect client to server with static.

    Args:
        file_type (choices): kernel|initrd|netboot - type of file
        deployment_id (string): deployment's UUID

    Returns:
        HttpResponse: redirect to file on static server

    Raises:
        Http404: if deployment with specified UUID doesn't exist

    """
    preboot = _get_preboot(deployment_id)
    file_url = preboot.get_file_url(file_type)
    if file_url is None:
        logger.warning('File {} for deployment {} doesn\'t exist'.format(
            file_type, deployment_id
        ))
        raise Http404
    return HttpResponseRedirect(file_url)


def done_ping(request, deployment_id):
    """View mark specified deployment (by UUID from URL) as finished.

    Args:
        deployment_id (string): deployment's UUID

    Returns:
        HttpResponse: document with 'marked' sentence
    """
    preboot = _get_preboot(deployment_id)
    preboot.increment_used_counter()
    ip = get_client_ip(request)
    Deployment.mark_as_done(deployment_id)
    logger.info(
        'Deployment {} for {} marked as done.'.format(
            deployment_id, ip
        )
    )
    return HttpResponse('marked', content_type='text/plain')
