# -*- coding: utf-8 -*-
import logging
import uuid
from datetime import date

from dateutil.parser import parse
from dj.choices import Choices
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.db.models.query import QuerySet
from django.utils.translation import ugettext_lazy as _
from django_extensions.db.fields.json import JSONField

from ralph.lib.external_services.base import InternalService
from ralph.lib.metrics import statsd
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import TimeStampMixin

logger = logging.getLogger(__name__)

EXTERNAL_JOBS_METRIC_PREFIX = getattr(
    settings, 'EXTERNAL_JOBS_METRIC_PREFIX', 'jobs'
)
EXTERNAL_JOBS_METRIC_NAME_TMPL = getattr(
    settings, 'EXTERNAL_JOBS_METRIC_NAME_TMPL', '{prefix}.{job_name}.{action}'
)


def _get_user_from_request(request):
    if request and request.user and request.user.is_authenticated:
        return request.user


class JobStatus(Choices):
    _ = Choices.Choice

    QUEUED = _('queued')
    FINISHED = _('finished')
    FAILED = _('failed')
    STARTED = _('started')
    FROZEN = _('frozen')
    KILLED = _('killed')


JOB_NOT_ENDED_STATUSES = set(
    [JobStatus.QUEUED, JobStatus.STARTED, JobStatus.FROZEN]
)


class JobQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=JOB_NOT_ENDED_STATUSES)

    def inactive(self):
        return self.exclude(status__in=JOB_NOT_ENDED_STATUSES)


def collect_metrics(action):
    def wrapper(func):
        def wrapped(job, *args, **kwargs):
            metric_name = EXTERNAL_JOBS_METRIC_NAME_TMPL.format(
                prefix=EXTERNAL_JOBS_METRIC_PREFIX,
                job_name=job._get_metric_name(),
                action=action
            )
            statsd.incr(metric_name)
            return func(job, *args, **kwargs)
        return wrapped
    return wrapper


class Job(TimeStampMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = NullableCharField(max_length=200, null=True, blank=True)
    service_name = models.CharField(max_length=200, null=False, blank=False)
    _dumped_params = JSONField()
    status = models.PositiveIntegerField(
        verbose_name=_('job status'),
        choices=JobStatus(),
        default=JobStatus.QUEUED.id,
    )
    _params = None
    objects = JobQuerySet.as_manager()

    class Meta:
        app_label = 'external_services'

    def __str__(self):
        return '{} ({})'.format(self.service_name, self.id)

    @property
    def user(self):
        try:
            return self.params['_request__user']
        except KeyError:
            if self.username:
                try:
                    return get_user_model()._default_manager.get(
                        username=self.username
                    )
                except get_user_model().DoesNotExist:
                    pass
        return None

    @property
    def is_running(self):
        """
        Return True if job is not ended.
        """
        return self.status in JOB_NOT_ENDED_STATUSES

    @property
    def is_frozen(self):
        """
        Return True if job is frozen.
        """
        return self.status == JobStatus.FROZEN

    @property
    def is_killed(self):
        """
        Return True if job is killed.
        """
        return self.status == JobStatus.KILLED

    @property
    def params(self):
        """
        Should be called on job-side to extract params as they were passed to
        job.
        """
        if self._params is None:
            self._params = self._restore_params(self._dumped_params)
            logger.debug('{} restored into {}'.format(
                self._dumped_params, self._params
            ))
        return self._params

    def _get_metric_name(self):
        return self.service_name

    def _update_dumped_params(self):
        # re-save job to store updated params in DB
        self._dumped_params = self.prepare_params(**self.params)
        logger.debug('Updating _dumped_params to {}'.format(
            self._dumped_params
        ))
        self.save()

    @collect_metrics('start')
    def start(self):
        """
        Mark job as started.
        """
        logger.info('Starting job {}'.format(self))
        self.status = JobStatus.STARTED
        self.save()

    @collect_metrics('reschedule')
    def reschedule(self):
        """
        Reschedule the same job again.
        """
        # TODO: use rq scheduler
        self._update_dumped_params()
        logger.info('Rescheduling {}'.format(self))
        service = InternalService(self.service_name)
        job = service.run_async(job_id=self.id)
        return job

    @collect_metrics('freeze')
    def freeze(self):
        self._update_dumped_params()
        logger.info('Freezing job {}'.format(self))
        self.status = JobStatus.FROZEN
        self.save()

    @collect_metrics('unfreeze')
    def unfreeze(self):
        logger.info('Unfreezing {}'.format(self))
        service = InternalService(self.service_name)
        job = service.run_async(job_id=self.id)
        return job

    @collect_metrics('kill')
    def kill(self):
        logger.info('Kill job {}'.format(self))
        self.status = JobStatus.KILLED
        self.save()

    @collect_metrics('fail')
    def fail(self, reason=''):
        """
        Mark job as failed.
        """
        self._update_dumped_params()
        logger.info('Job {} has failed. Reason: {}'.format(self, reason))
        self.status = JobStatus.FAILED
        self.save()

    @collect_metrics('success')
    def success(self):
        """
        Mark job as successfuly ended.
        """
        self._update_dumped_params()
        logger.info('Job {} has succeeded'.format(self))
        self.status = JobStatus.FINISHED
        self.save()

    @classmethod
    def prepare_params(cls, **kwargs):
        user = kwargs.pop('requester', None)
        result = cls.dump_obj_to_jsonable(kwargs)
        result['_request__user'] = (
            result.get('_request__user') or
            (cls.dump_obj_to_jsonable(user) if user else None)
        )
        logger.debug('{} prepared into {}'.format(kwargs, result))
        return result

    @classmethod
    def run(cls, service_name, requester, defaults=None, **kwargs):
        """
        Run Job asynchronously in internal service (with DB and models access).
        """
        service = InternalService(service_name)
        obj = cls._default_manager.create(
            service_name=service_name,
            username=requester.username if requester else None,
            _dumped_params=cls.prepare_params(requester=requester, **kwargs),
            **(defaults or {})
        )
        # commit transaction to allow worker to fetch it using job id
        transaction.commit()
        service.run_async(job_id=obj.id)
        return obj.id, obj

    @classmethod
    def dump_obj_to_jsonable(cls, obj):
        """
        Dump obj to JSON-acceptable format
        """
        result = obj
        if isinstance(obj, (list, tuple, set)):
            result = [cls.dump_obj_to_jsonable(p) for p in obj]
        elif isinstance(obj, QuerySet):
            result = {
                '__django_queryset': True,
                'value': [i.pk for i in obj],
                'content_type_id': ContentType.objects.get_for_model(
                    obj.model
                ).pk
            }
        elif isinstance(obj, date):
            result = {
                '__date': True,
                'value': str(obj)
            }
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
    def _restore_params(cls, obj):
        return cls._restore_django_models(obj)

    @classmethod
    def _restore_django_models(cls, obj):
        """
        Restore Django objects from dump created with `dump_obj_to_jsonable`
        """
        result = obj
        if isinstance(obj, (list, tuple)):
            result = [cls._restore_django_models(p) for p in obj]
        elif isinstance(obj, dict):
            if obj.get('__date') is True:
                result = parse(obj.get('value')).date()
            elif obj.get('__django_queryset') is True:
                ct = ContentType.objects.get_for_id(obj['content_type_id'])
                result = ct.model_class().objects.filter(
                    pk__in=obj.get('value')
                )
            elif obj.get('__django_model') is True:
                ct = ContentType.objects.get_for_id(obj['content_type_id'])
                result = ct.get_object_for_this_type(pk=obj['object_pk'])
            else:
                result = {}
                for k, v in obj.items():
                    result[k] = cls._restore_django_models(v)
        return result
