# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.core.management.base import BaseCommand
from django.utils.log import dictConfig
from django_rq.workers import get_worker
from redis.exceptions import ConnectionError
from rq import use_connection

from ralph.notifications.error_handlers import notifications_error_handler
from ralph.notifications.conf import QUEUE_NAME


logger = logging.getLogger('rq.worker')
if not logger.handlers:
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "rq_console": {
                "format": "%(asctime)s %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "rq_console": {
                "level": "DEBUG",
                "class": "rq.utils.ColorizingStreamHandler",
                "formatter": "rq_console",
                "exclude": ["%(asctime)s"],
            },
        },
        "worker": {
            "handlers": ["rq_console"],
            "level": "DEBUG"
        },
    })


class Command(BaseCommand):
    help = 'Runs RQ worker for notifications.'

    def handle(self, *args, **kwargs):
        try:
            worker = get_worker(QUEUE_NAME)
            use_connection(worker.connection)
            worker.push_exc_handler(notifications_error_handler)
            worker.work()
        except ConnectionError as e:
            raise SystemExit(e)
