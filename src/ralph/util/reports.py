# -*- coding: utf-8 -*-
"""Utilities for asynchronous reports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

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
        return self._full_path



class Report(View):
    """Base class for asynchronous reports. It works as a view."""

    QUEUE_NAME = 'default'
    get_result = None
    get_response = None

    def __init__(self, get_result, get_response, **kwargs):
        self._jobid = None
        self._job = None
        self.get_result = get_result
        self.get_response = get_response
        self.connection = django_rq.get_connection(self.QUEUE_NAME)
        self.queue = django_rq.get_queue(self.QUEUE_NAME)
        super(Report, self).__init__(**kwargs)

    @property
    def jobid(self):
        if self._jobid:
            return self._jobid
        else:
            self._jobid = rq.get_current_job()

    @property
    def job(self):
        return rq.job.Job.fetch(self.jobid, connection=self.connection)

    @property
    def progress(self):
        return None

    @property
    def eta(self):
        return None


    def get(self, request, *args, **kwargs):
        jobid = request.GET.get('_report_jobid')
        if jobid is None:
            job = self.queue.enqueue(
                    self.get_result, PicklableRequest(request),
                    *args, **kwargs)
            result = json.dumps({'jobid': job.id})
            return HttpResponse(result, content_type='application/json')
        else:
            self._jobid = jobid
            result = self.job.result
            if request.GET.get('_report_finish'):
                if result is None:
                    # Shouldn't happen if browser side is OK
                    return HttpResponseBadRequest()
                else:
                    return self.get_response(request, result)
            else:
                if result is None:
                    result = json.dumps({
                        'jobid': self.job.id,
                        'progress': self.progress,
                        'eta': self.eta,
                        'finished': False,
                    })
                else:
                    result = json.dumps({
                        'jobid': self.job.id,
                        'progress': 100,
                        'eta': {'hours': 0, 'minutes': 0, 'seconds': 0},
                        'finished': True,
                    })
            return HttpResponse(result, content_type='application/json')
