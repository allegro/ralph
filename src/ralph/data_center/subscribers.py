# -*- coding: utf-8 -*-
import logging
from contextlib import ExitStack
from functools import wraps

import pyhermes
from django.db import OperationalError, transaction

from ralph.data_center.models import (
    Cluster,
    ClusterType,
    VIP,
    VIPProtocol,
)
from ralph.ralph2_sync.helpers import WithSignalDisabled

logger = logging.getLogger(__name__)


def _get_publisher_signal_info(func):
    """
    Return signal info for publisher in format accepted by `WithSignalDisabled`.
    """
    return {
        'dispatch_uid': func._signal_dispatch_uid,
        'sender': func._signal_model,
        'signal': func._signal_type,
        'receiver': func,
    }


# XXX remove/rename stuff related to ralph2 sync
class sync_subscriber(pyhermes.subscriber):
    """
    Log additional exception when sync has failed.
    """
    def __init__(self, topic, disable_publishers=None):
        self.disable_publishers = disable_publishers or []
        super().__init__(topic)

    def _get_wrapper(self, func):
        @wraps(func)
        @transaction.atomic
        def exception_wrapper(*args, **kwargs):
            # disable selected publisher signals during handling subcriber
            with ExitStack() as stack:
                for publisher in self.disable_publishers:
                    stack.enter_context(WithSignalDisabled(
                        **_get_publisher_signal_info(publisher)
                    ))
                try:
                    return func(*args, **kwargs)
                except (OperationalError, ) as e:
                    logger.exception(
                        'Exception during syncing: {}'.format(str(e))
                    )
                    raise  # return 500 to retry on hermes
                except Exception as e:
                    logger.exception(
                        'Exception during syncing {}'.format(str(e))
                    )
        return exception_wrapper


@sync_subscriber(
    topic='createVipEvent',
)
def handle_create_vip_event(data):
    try:
        vip = VIP.objects.get(name=data['name'])
    except VIP.DoesNotExist:
        pass
    else:
        # XXX is it OK just to ignore such case?
        logger.warning(
            'VIP with name "{}" already exists. Ignoring.'.format(data['name'])
        )
        return
    protocol = getattr(
        VIPProtocol, data['protocol'].lower(), VIPProtocol.unknown
    )
    cluster_type, _ = ClusterType.objects.get_or_create(
        name=data['load_balancer_type']
    )
    cluster, _ = Cluster.objects.get_or_create(
        name=data['load_balancer'],
        type=cluster_type,
    )
    vip = VIP(
        name = data['name'],
        port = data['port'],
        protocol = protocol,
        parent = cluster,
        # XXX add service as well
    )
    vip.save()
