# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django_rq

from ralph.notifications import send_email_notification
from ralph.notifications.conf import (
    NOTIFICATIONS_MAX_ATTEMPTS,
    NOTIFICATIONS_QUEUE_NAME,
)


def notifications_error_handler(job, exc_type, exc_value, traceback):
    attempt = job.meta.get('attempt', 1)
    if attempt >= NOTIFICATIONS_MAX_ATTEMPTS:
        return True  # fall through to the next exception handler on the stack
    attempt += 1
    queue = django_rq.get_queue(name=NOTIFICATIONS_QUEUE_NAME)
    new_job = queue.enqueue_call(
        func=send_email_notification,
        kwargs={
            'notification_id': job.kwargs['notification_id'],
        },
        timeout=120,
        result_ttl=0,
    )
    new_job.meta['attempt'] = attempt
    new_job.save()
    return False
