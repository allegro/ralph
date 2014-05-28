# -*- coding: utf-8 -*-
"""Utilities for asynchronous reports."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime
import django_rq
import importlib
import json
import rq
import copy

from django.conf import settings
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import resolve
from django.views.generic.base import View
from django.http import HttpResponse, HttpResponseBadRequest


class PicklableRequest(object):

    """A class that mimics the django Request object, but only contains
    picklable data, so it can be put on rq."""

    def __init__(self, request):
        self.method = request.method
        self.GET = request.GET
        self.path = request.path
        self._full_path = request.get_full_path()
        self.COOKIES = request.COOKIES

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
    return (1.0 - job.meta['progress']) / velocity


def get_result(request):
    url_match = resolve(request.path)
    module = importlib.import_module(url_match.func.__module__)
    view = getattr(module, url_match.func.__name__)()
    request = copy.deepcopy(request)
    SessionMiddleware().process_request(request)
    AuthenticationMiddleware().process_request(request)
    view.request = request
    return view.get_result(
        request, *url_match.args, **url_match.kwargs
    )


def set_progress(job, progress):
    """Set the progress of a job and save. If job is None - do nothing"""
    if job:
        job.meta['progress'] = progress
        if not job.meta['start_progress']:
            job.meta['start_progress'] = datetime.datetime.now()
        job.save()


# This is removed as top-level function so rq can find it
def enqueue(view, request):
    return view.queue.enqueue_call(
        func=get_result,
        args=(PicklableRequest(request),),
        timeout=settings.RQ_TIMEOUT,
    )


class Report(View):

    """Base class for asynchronous reports. It works as a view."""
    QUEUE_NAME = 'reports'

    def is_async(self, request, *args, **kwargs):
        return 'export' in request.GET

    def __init__(self, **kwargs):
        self.connection = django_rq.get_connection(self.QUEUE_NAME)
        self.queue = django_rq.get_queue(self.QUEUE_NAME)
        super(Report, self).__init__(**kwargs)

    def get_async(self, request, *args, **kwargs):
        jobid = request.GET.get('_report_jobid')
        if jobid is None:
            job = enqueue(self, request)
            job.meta['progress'] = 0
            job.meta['start_progress'] = None
            job.meta['start'] = datetime.datetime.now()
            job.save()
            result = json.dumps({'jobid': job.id})
            return HttpResponse(result, content_type='application/json')
        else:
            job = rq.job.Job.fetch(jobid, connection=self.connection)
            result = job.result
            if job.exc_info is not None:
                json_result = json.dumps({
                    'jobid': jobid,
                    'progress': 1,
                    'eta': {'hours': 0, 'minutes': 0, 'seconds': 0},
                    'finished': True,
                    'failed': True,
                })
            elif request.GET.get('_report_finish'):
                if result is None:
                    # Shouldn't happen if browser side is OK
                    return HttpResponseBadRequest()
                else:
                    return self.get_response(request, result)
            else:
                if result is None:
                    json_result = json.dumps({
                        'jobid': jobid,
                        'progress': get_progress(job),
                        'eta': get_eta(job),
                        'finished': False,
                        'failed': False,
                    })
                else:
                    json_result = json.dumps({
                        'jobid': jobid,
                        'progress': 100,
                        'eta': {'hours': 0, 'minutes': 0, 'seconds': 0},
                        'finished': True,
                        'failed': False,
                    })
            return HttpResponse(json_result, content_type='application/json')

    def get(self, request, *args, **kwargs):
        """Perform the GET request."""
        if self.is_async(request, *args, **kwargs):
            return self.get_async(request, *args, **kwargs)
        else:
            return super(Report, self).get(request, *args, **kwargs)
