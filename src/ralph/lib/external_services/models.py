# -*- coding: utf-8 -*-
import logging
import uuid

from dj.choices import Choices
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField

from ralph.lib.external_services.base import InternalService
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import TimeStampMixin

logger = logging.getLogger(__name__)


def _get_user_from_request(request):
    if request and request.user and request.user.is_authenticated():
        return request.user


class JobStatus(Choices):
    _ = Choices.Choice

    QUEUED = _('queued')
    FINISHED = _('finished')
    FAILED = _('failed')
    STARTED = _('started')


class Job(TimeStampMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = NullableCharField(max_length=200, null=True, blank=True)
    service_name = models.CharField(max_length=200, null=False, blank=False)
    _dumped_params = JSONField()
    status = models.PositiveIntegerField(
        verbose_name=_('job status'),
        choices=JobStatus(),
        default=JobStatus.QUEUED.id,
    )
    _params = None

    class Meta:
        app_label = 'external_services'

    def __str__(self):
        return '{} ({})'.format(self.service_name, self.id)

    @property
    def is_running(self):
        """
        Return True if job is not ended.
        """
        return self.status not in (JobStatus.FINISHED, JobStatus.FAILED)

    @property
    def params(self):
        """
        Should be called on job-side to extract params as they were passed to
        job.
        """
        if self._params is None:
            self._params = self._restore_django_models(self._dumped_params)
        return self._params

    def reschedule(self):
        """
        Reschedule the same job again.
        """
        # TODO: use rq scheduler
        logger.info('Rescheduling {}'.format(self))
        service = InternalService(self.service_name)
        job = service.run_async(job_id=self.id)
        return job

    def fail(self, reason=''):
        """
        Mark job as failed.
        """
        logger.info('Job {} has failed. Reason: {}'.format(self, reason))
        self.status = JobStatus.FAILED
        self.save()

    def success(self):
        """
        Mark job as successfuly ended.
        """
        logger.info('Job {} has succeeded'.format(self))
        self.status = JobStatus.FINISHED
        self.save()

    @classmethod
    def prepare_params(cls, **kwargs):
        request = kwargs.pop('request', None)
        result = cls.dump_obj_to_jsonable(kwargs)
        user = _get_user_from_request(request)
        if user:
            result['_request__user'] = cls.dump_obj_to_jsonable(user)
        return result

    @classmethod
    def run(cls, service_name, defaults=None, **kwargs):
        """
        Run Job asynchronously in internal service (with DB and models access).
        """
        service = InternalService(service_name)
        user = _get_user_from_request(kwargs.get('request'))
        obj = cls._default_manager.create(
            service_name=service_name,
            user=user.username if user else None,
            _dumped_params=cls.prepare_params(**kwargs),
            **(defaults or {})
        )
        service.run_async(job_id=obj.id)
        return obj.id, obj

    @classmethod
    def dump_obj_to_jsonable(cls, obj):
        """
        Dump obj to JSON-acceptable format
        """
        result = obj
        if isinstance(obj, (list, tuple)):
            result = [cls.dump_obj_to_jsonable(p) for p in obj]
        elif isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                result[k] = cls.dump_obj_to_jsonable(v)
        elif isinstance(obj, models.Model):
            # save Django object as 3-items dict with content type and object id
            result = {
                '__django_model': True,
                'content_type_id': ContentType.objects.get_for_model(obj).pk,
                'object_pk': obj.pk,
            }
        return result

    @classmethod
    def _restore_django_models(cls, obj):
        """
        Restore Django objects from dump created with `dump_obj_to_jsonable`
        """
        result = obj
        if isinstance(obj, (list, tuple)):
            result = [cls._restore_django_models(p) for p in obj]
        elif isinstance(obj, dict):
            if obj.get('__django_model') is True:
                ct = ContentType.objects.get_for_id(obj['content_type_id'])
                result = ct.get_object_for_this_type(pk=obj['object_pk'])
            else:
                result = {}
                for k, v in obj.items():
                    result[k] = cls._restore_django_models(v)
        return result
