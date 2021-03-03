# -*- coding: utf-8 -*-
import json

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase, TransactionTestCase
from djmoney.money import Money

from ralph.lib.external_services.models import Job, JobStatus
from ralph.tests.models import Bar, Foo


def test_job_func(job_id):
    job = Job.objects.get(pk=job_id)
    foo = job.params['foo']
    foo.bar = 'barbar'
    foo.save()
    Bar.objects.create(
        name=job.params['_request__user'].username,
        date='2016-03-30',
        price=Money(100, 'XXX')
    )
    job.success()


class JobDumpParamsTestCase(TestCase):
    def setUp(self):
        self.foo = Foo.objects.create(bar='abc')
        self.bar = Bar.objects.create(
            name='bar', date='2016-03-03', price=Money(10, 'XXX')
        )
        self.foo_content_type_id = ContentType.objects.get_for_model(self.foo).pk  # noqa
        self.bar_content_type_id = ContentType.objects.get_for_model(self.bar).pk  # noqa

        self.foo_dump = {
            '__django_model': True,
            'object_pk': self.foo.id,
            'content_type_id': self.foo_content_type_id,
        }
        self.bar_dump = {
            '__django_model': True,
            'object_pk': self.bar.id,
            'content_type_id': self.bar_content_type_id,
        }

        self.sample_obj = {
            'foo1': self.foo,
            'l': [self.foo, {'d': self.bar}],
            'd': {'d1': [self.bar]},
        }
        self.sample_obj_dump = {
            'foo1': self.foo_dump,
            'l': [self.foo_dump, {'d': self.bar_dump}],
            'd': {'d1': [self.bar_dump]}
        }

    def test_dump_django_model(self):
        result = Job.dump_obj_to_jsonable(self.foo)
        self.assertEqual(result, self.foo_dump)

    def test_dump_params(self):
        result = Job.dump_obj_to_jsonable(self.sample_obj)
        self.assertEqual(result, self.sample_obj_dump)

    def test_dump_is_jsonable(self):
        dump = Job.dump_obj_to_jsonable(self.sample_obj)
        json.dumps(dump)

    def test_restore_django_model(self):
        result = Job._restore_django_models(self.foo_dump)
        self.assertEqual(result, self.foo)

    def test_restore_params(self):
        result = Job._restore_django_models(self.sample_obj_dump)
        self.assertEqual(result, self.sample_obj)


class JobRunTestCase(TransactionTestCase):
    def setUp(self):
        self.foo = Foo.objects.create(bar='bar')
        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('/')
        self.user = get_user_model().objects.create_user(
            username='test1',
            password='password',
        )
        self.request.user = self.user

    def test_job(self):
        prev_bar_count = Bar.objects.count()
        # this job should be executed synchronously since queue for JOB_TEST
        # service is configured with ASYNC=False (just for testing)
        job_id, job = Job.run(
            'JOB_TEST', requester=self.user, foo=self.foo
        )
        job.refresh_from_db()
        self.foo.refresh_from_db()

        self.assertEqual(job.status, JobStatus.FINISHED.id)
        self.assertEqual(Bar.objects.count(), prev_bar_count + 1)
        self.assertEqual(self.foo.bar, 'barbar')
        self.assertTrue(Bar.objects.filter(name='test1').exists())
