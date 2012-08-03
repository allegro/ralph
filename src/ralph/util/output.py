#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import subprocess
import sys

from django.conf import settings
from django.core.mail import mail_admins
from lck import git

import ralph


BOILERPLATE = 20
try:
    COLUMNS = int(os.popen('stty size', 'r').read().split()[1])
except IndexError:
    # script ran from a daemon, without a STTY. No padding.
    WIDTH = 0
else:
    WIDTH = COLUMNS - BOILERPLATE
HOSTNAME = subprocess.check_output(['hostname', '-f']).strip()
GIT_VERSION = git.get_version(os.path.dirname(__file__))
RELEASE_VERSION = ".".join(str(num) for num in ralph.VERSION)
VERSION = GIT_VERSION or RELEASE_VERSION
CELERY_SEND_TASK_ERROR_EMAILS = getattr(settings,
    'CELERY_SEND_TASK_ERROR_EMAILS', False)


def get(interactive, err=False, verbose=False):
    """Support for simple stdout logging while executing the task. Useful for
    interactive execution. If not interactive, returns a stub that logs to
    file."""
    logger = logging.getLogger(__name__)
    logging_buffer = []
    def logging_stdout(*args, **kwargs):
        logging_buffer.append(" ".join(args))
        end = kwargs.get('end')
        if end:
            logging_buffer.append(end)
        if end in (None, '\r', '\n', '\r\n'):
            message = "".join(logging_buffer).strip()
            if err:
                logger.error(message)
                if CELERY_SEND_TASK_ERROR_EMAILS:
                    subject = '[{}] {}'.format(HOSTNAME,
                        message.split(':', 1)[0])
                    mail_admins(subject, message + '\t \n\t \n' + VERSION)
            elif verbose:
                logger.debug(message)
            else:
                logger.info(message)
            logging_buffer[:] = ()
    def actual_stdout(*args, **kwargs):
        print(*args, file=sys.stdout if not err else sys.stderr, **kwargs)
        sys.stdout.flush()
        sys.stderr.flush()
    return actual_stdout if interactive else logging_stdout
