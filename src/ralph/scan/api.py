# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import traceback

import django_rq
from django.conf import settings
from lck.django.common import remote_addr
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.cache import SimpleCache
from tastypie.bundle import Bundle
from tastypie.resources import Resource
from tastypie.throttle import CacheThrottle

from ralph.scan.manual import scan_address_job


API_THROTTLE_AT = settings.API_THROTTLING['throttle_at']
API_TIMEFRAME = settings.API_THROTTLING['timeframe']
API_EXPIRATION = settings.API_THROTTLING['expiration']


logger = logging.getLogger(__name__)


class JobObject(object):
    __slots__ = ['job_id']

    def __init__(self, job_id=None):
        self.job_id = job_id


def store_device_data(data):
    """
    Queues function that append data from external plugin to data from other
    sources.
    """

    queue = django_rq.get_queue()
    job = queue.enqueue_call(
        func=scan_address_job,
        kwargs={
            'results': data,
        },
        timeout=300,
        result_ttl=86400,
    )
    return JobObject(job.id)


class ExternalPluginResource(Resource):
    job_id = fields.CharField(attribute='job_id')

    def obj_create(self, bundle, **kwargs):
        remote_ip = remote_addr(bundle.request)
        logger.debug('Received JSON data (remote IP: %s): %s' % (
            remote_ip,
            bundle.data.get('data'),
        ))
        try:
            bundle.obj = store_device_data({
                'donpedro': bundle.data.get('data'),
            })
        except Exception:
            logger.exception('An exception occurred (remote IP: %s): %s' % (
                remote_ip,
                traceback.format_exc(),
            ))
            raise
        return bundle

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.job_id
        else:
            kwargs['pk'] = bundle_or_obj.job_id
        return kwargs

    class Meta:
        resource_name = 'scanresult'
        object_class = JobObject
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()
        filtering = {}
        cache = SimpleCache()
        throttle = CacheThrottle(
            throttle_at=API_THROTTLE_AT,
            timeframe=API_TIMEFRAME,
            expiration=API_EXPIRATION,
        )
        allowed_methods = ['post']
