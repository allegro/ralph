# -*- coding: utf-8 -*-

"""
Save merged scan results data.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django_rq
import time

from django.conf import settings


def _save_job_results(job_id, start_ts):
    if (int(time.time()) - start_ts) > 86100:  # 24h - 5min
        return
    # todo


def save_job_results(job_id):
    queue_name = 'default'
    if 'scan_automerger' in settings.RQ_QUEUES:
        queue_name = 'scan_automerger'
    queue = django_rq.get_queue(queue_name)
    queue.enqueue_call(
        func=_save_job_results,
        kwargs={
            'job_id': job_id,
            'start_ts': int(time.time()),
        },
        timeout=300,
        result_ttl=0,
    )
