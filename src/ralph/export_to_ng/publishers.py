import logging
from functools import wraps

import pyhermes
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from pyhermes import publisher

from ralph.discovery.models import Device

logger = logging.getLogger(__name__)


def ralph3_sync(model):
    """
    Decorator for synchronizers with Ralph3. Decorated function should return
    dict with event data. Decorated function name is used as a topic name and
    dispatch_uid for post_save signal.
    """
    def wrap(func):
        @wraps(func)
        # connect to post_save signal for a model
        @receiver(
            post_save, sender=model, dispatch_uid=func.__name__,
        )
        # register publisher
        @pyhermes.publisher(topic=func.__name__)
        def wrapped_func(sender, instance=None, created=False, **kwargs):
            if (
                # publish only if sync enabled (globally and for particular
                # function)
                settings.RALPH3_HERMES_SYNC_ENABLED and
                func.__name__ in settings.RALPH3_HERMES_SYNC_FUNCTIONS and
                # process the signal only if instance has not attribute
                # `_handle_post_save` set to False
                getattr(instance, '_handle_post_save', True)
            ):
                try:
                    result = func(sender, instance, created, **kwargs)
                    if result:
                        pyhermes.publish(func.__name__, result)
                except:
                    logger.exception('Error during Ralph2 sync')
                else:
                    return result
        return wrapped_func
    return wrap


@publisher(topic='ralph2_sync_ack', auto_publish_result=True)
def publish_sync_ack_to_ralph3(obj, ralph3_id):
    """
    Publish ACK to Ralph3 that some object was updated.
    """
    return {
        'model': obj._meta.object_name,
        'id': obj.id,
        'ralph3_id': ralph3_id,
    }


@ralph3_sync(Device)
def sync_device_to_ralph3(sender, instance=None, created=False, **kwargs):
    device = instance
    asset = device.get_asset()
    if not asset:
        return {}
    mgmt_ip = device.management_ip
    data = {
        'id': asset.id,
        'hostname': device.name,
        'management_ip': mgmt_ip.address if mgmt_ip else '',
        'management_hostname': mgmt_ip.hostname if mgmt_ip else '',
        'service': device.service.uid if device.service else None,
        'environment': device.device_environment_id,
    }
    return data
