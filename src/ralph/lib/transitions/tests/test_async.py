"""
Test asynchronous transitions
"""
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from ralph.lib.external_services.models import JobStatus
from ralph.lib.transitions.models import run_transition, TransitionJob
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests.models import AsyncOrder, Foo, OrderStatus


class AsyncTransitionsTest(TransitionTestCase):

    def setUp(self):
        super().setUp()
        self.request = RequestFactory()
        self.request.user = get_user_model().objects.create_user(
            username='test1',
            password='password',
        )
        self.foo = Foo.objects.create(bar='123')

    def test_run_action_during_async_transition(self):
        async_order = AsyncOrder.objects.create(name='test')
        _, transition, _ = self._create_transition(
            model=async_order, name='prepare',
            source=[OrderStatus.new.id], target=OrderStatus.to_send.id,
            actions=['long_running_action'],
            async_service_name='ASYNC_TRANSITIONS',
        )
        job_id = run_transition(
            instances=[async_order],
            transition_obj_or_name=transition,
            request=self.request,
            field='status',
            data={'name': 'abc'}
        )[0]
        job = TransitionJob.objects.get(pk=job_id)
        async_order.refresh_from_db()
        self.assertEqual(job.status, JobStatus.FINISHED.id)
        self.assertEqual(async_order.counter, 2)
        self.assertEqual(async_order.name, 'abc')
        # TODO: test status

    def test_rescheduling_action_during_async_transition(self):
        async_order = AsyncOrder.objects.create(name='test')
        async_order2 = AsyncOrder.objects.create(name='test2')
        async_order3 = AsyncOrder.objects.create(name='test3')
        async_orders = [async_order, async_order2, async_order3]
        _, transition, _ = self._create_transition(
            model=async_order, name='prepare',
            source=[OrderStatus.new.id], target=OrderStatus.to_send.id,
            actions=[
                'long_running_action',
                'long_running_action_with_precondition',
                'assing_user',
            ],
            async_service_name='ASYNC_TRANSITIONS',
        )
        job_ids = run_transition(
            instances=async_orders,
            transition_obj_or_name=transition,
            request=self.request,
            field='status',
            data={'name': 'def', 'foo': self.foo}
        )
        for job_id, async_order in zip(job_ids, async_orders):
            job = TransitionJob.objects.get(pk=job_id)
            async_order.refresh_from_db()
            self.assertEqual(job.status, JobStatus.FINISHED.id)
            self.assertEqual(async_order.counter, 5)
            self.assertEqual(async_order.name, 'def')
            self.assertEqual(async_order.username, 'test1')

    def test_run_failing_async_transition(self):
        async_order = AsyncOrder.objects.create(name='test')
        async_order2 = AsyncOrder.objects.create(name='test')
        _, transition, _ = self._create_transition(
            model=async_order, name='prepare',
            source=[OrderStatus.new.id], target=OrderStatus.to_send.id,
            actions=['failing_action'],
            async_service_name='ASYNC_TRANSITIONS',
        )
        job_ids = run_transition(
            instances=[async_order, async_order2],
            transition_obj_or_name=transition,
            request=self.request,
            field='status',
            data={'name': 'def', 'foo': self.foo}
        )
        for job_id in job_ids:
            job = TransitionJob.objects.get(pk=job_id)
            self.assertEqual(job.status, JobStatus.FAILED.id)
