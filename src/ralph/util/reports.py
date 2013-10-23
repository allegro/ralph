# -*- coding: utf-8 -*-
"""Utilities for asynchronous reports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import rq
import django_rq
import json
from django.views.generic.base import View
from django.http import HttpResponse, HttpResponseBadRequest


class PicklableRequest(object):
    """A class that mimics the django Request object, but only contains
    picklable data, so it can be put on rq."""

    def __init__(self, request):
        self.method = request.method
        self.GET = request.GET
        self._full_path = request.get_full_path()

    def get_full_path(self):
        """Returns the full url of this request."""
        return self._full_path

def get_progress(job):
    """Returns job progress in percent"""
    return int(job.meta['progress'] * 100)

def get_eta(job):
    """Returns job ETA in seconds"""
    if not job.meta['progress'] or not job.meta['start_progress']:
        return None
    velocity = job.meta['progress'] / (
            datetime.datetime.now() - job.meta['start_progress']
    ).total_seconds()
    return  (1.0 - job.meta['progress']) / velocity


class Report(View):
    """Base class for asynchronous reports. It works as a view."""

    QUEUE_NAME = 'default'
    get_result = None
    get_response = None

    def __init__(self, get_result, get_response, **kwargs):
        self.get_result = get_result
        self.get_response = get_response
        self.connection = django_rq.get_connection(self.QUEUE_NAME)
        self.queue = django_rq.get_queue(self.QUEUE_NAME)
        super(Report, self).__init__(**kwargs)



    def get(self, request, *args, **kwargs):
        """Perform the GET request."""
        jobid = request.GET.get('_report_jobid')
        if jobid is None:
            job = self.queue.enqueue(
                    self.get_result, PicklableRequest(request),
                    *args, **kwargs)
            job.meta['progress'] = 0
            job.meta['start_progress'] = None
            job.meta['start'] = datetime.datetime.now()
            job.save()
            result = json.dumps({'jobid': job.id})
            return HttpResponse(result, content_type='application/json')
        else:
            job = rq.job.Job.fetch(jobid, connection=self.connection)
            result = job.result
            if request.GET.get('_report_finish'):
                if result is None:
                    # Shouldn't happen if browser side is OK
                    return HttpResponseBadRequest()
                else:
                    return self.get_response(request, result)
            else:
                if result is None:
                    result = json.dumps({
                        'jobid': jobid,
                        'progress': get_progress(job),
                        'eta': get_eta(job),
                        'finished': False,
                    })
                else:
                    result = json.dumps({
                        'jobid': jobid,
                        'progress': 100,
                        'eta': {'hours': 0, 'minutes': 0, 'seconds': 0},
                        'finished': True,
                    })
            return HttpResponse(result, content_type='application/json')
