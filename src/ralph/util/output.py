#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import sys


def get(interactive, err=False):
    """Support for simple stdout logging while executing the task. Useful for
    interactive execution. If not interactive, returns a stub that logs to
    file."""
    logger = logging.getLogger(__name__)
    logging_buffer = []

    def logging_stdout(*args, **kwargs):
        logging_buffer.append(" ".join(args))
        end = kwargs.get('end')
        verbose = kwargs.get('verbose')
        if end:
            logging_buffer.append(end)
        if end in (None, '\r', '\n', '\r\n'):
            message = "".join(logging_buffer).strip()
            if err:
                logger.error(message)
            elif verbose:
                logger.debug(message)
            else:
                logger.info(message)
            logging_buffer[:] = ()

    def actual_stdout(*args, **kwargs):
        try:
            del kwargs['verbose']
        except KeyError:
            pass
        print(*args, file=sys.stdout if not err else sys.stderr, **kwargs)
        sys.stdout.flush()
        sys.stderr.flush()

    return actual_stdout if interactive else logging_stdout
