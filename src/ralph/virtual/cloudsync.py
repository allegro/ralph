import json
import logging
import threading

import pkg_resources
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound
)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ralph.virtual.models import CloudProvider

logger = logging.getLogger(__name__)


ENTRY_POINTS_GROUP = "ralph.cloud_sync_processors"
CLOUD_SYNC_DRIVERS = None
LOCK = threading.Lock()


def load_processors():
    global CLOUD_SYNC_DRIVERS

    # NOTE(romcheg): Check if processors were loaded prior to locking anything.
    if CLOUD_SYNC_DRIVERS is not None:
        return

    with LOCK:
        # NOTE(romcheg): Double check in order to avoid race conditions.
        if CLOUD_SYNC_DRIVERS is not None:
            return

        logger.info("Loading cloud sync processors.")

        CLOUD_SYNC_DRIVERS = {}

        for ep in pkg_resources.iter_entry_points(ENTRY_POINTS_GROUP):
            try:
                CLOUD_SYNC_DRIVERS[ep.name] = ep.resolve()
            except ImportError:
                logger.error(
                    "Could not import DC asset event processor from %s.", ep.module_name
                )


@csrf_exempt
@require_POST
def cloud_sync_router(request, cloud_provider_id):
    load_processors()

    raw_data = request.read().decode("utf-8")

    try:
        event_data = json.loads(raw_data)
    except ValueError:
        return HttpResponseBadRequest("Content must be a valid JSON text.")

    try:
        cloud_provider = CloudProvider.objects.get(
            Q(
                pk=cloud_provider_id,
                cloud_sync_enabled=True,
                cloud_sync_driver__isnull=False,
            )
            & ~Q(cloud_sync_driver="")
        )

        processor = CLOUD_SYNC_DRIVERS[cloud_provider.cloud_sync_driver]
    except CloudProvider.DoesNotExist:
        return HttpResponseNotFound()
    except KeyError:
        return HttpResponse("Specified processor is not available", status=501)

    processor(cloud_provider, event_data)

    return HttpResponse(status=204)
