"""
Test asynchronous transitions
"""
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TransactionTestCase

from ralph.lib.external_services.models import JobStatus
from ralph.lib.transitions.models import (
    run_transition,
    TransitionJob,
    TransitionsHistory
)
from ralph.lib.transitions.tests import TransitionTestCaseMixin
from ralph.tests.models import AsyncOrder, Foo, OrderStatus


class AsyncTransitionsTest(TransitionTestCaseMixin, TransactionTestCase):

    def setUp(self):
        super().setUp()
        self.request = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username='test1',
            password='password',
        )
        self.request.user = self.user
        self.foo = Foo.objects.create(bar='123')

    def test_run_action_during_async_transition(self):
        async_order = AsyncOrder.objects.create(name='test')
        old_status_id = async_order.status
        _, transition, _ = self._create_transition(
            model=async_order, name='prepare',
            source=[OrderStatus.new.id], target=OrderStatus.to_send.id,
            actions=['long_running_action'],
            async_service_name='ASYNC_TRANSITIONS',
        )
        job_id = run_transition(
            instances=[async_order],
            transition_obj_or_name=transition,
            requester=self.user,
            field='status',
            data={'name': 'abc'}
        )[0]
        job = TransitionJob.objects.get(pk=job_id)

        async_order.refresh_from_db()
        self.assertEqual(job.status, JobStatus.FINISHED.id)
        self.assertEqual(async_order.counter, 2)
        self.assertEqual(async_order.name, 'abc')
        self.assertNotEqual(async_order.status, old_status_id)

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
            requester=self.user,
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
            # check if shared params and history kwargs are properly stored
            # during rescheduling
            self.assertEqual(
                job.params['shared_params'][async_order.pk]['counter'], 5
            )
            self.assertEqual(
                job.params['history_kwargs'][async_order.pk]['hist_counter'], 5
            )
            # check history entries
            th = TransitionsHistory.objects.get(object_id=async_order.id)
            self.assertEqual(th.kwargs, {'hist_counter': 5})
            self.assertEqual(th.logged_user_id, self.request.user.pk)
            self.assertCountEqual(
                th.actions,
                [
                    "Assign user",
                    "Long running action",
                    "Another long running action"
                ]
            )

    def test_freezing_action_during_async_transition(self):
        async_order = AsyncOrder.objects.create(name='test')
        async_order2 = AsyncOrder.objects.create(name='test3')
        async_orders = [async_order, async_order2]
        _, transition, _ = self._create_transition(
            model=async_order, name='prepare',
            source=[OrderStatus.new.id], target=OrderStatus.to_send.id,
            actions=[
                'freezing_action',
                'long_running_action',
                'assing_user',
            ],
            async_service_name='ASYNC_TRANSITIONS',
        )
        job_ids = run_transition(
            instances=async_orders,
            transition_obj_or_name=transition,
            requester=self.user,
            field='status',
            data={'name': 'def', 'foo': self.foo}
        )
        for job_id, async_order in zip(job_ids, async_orders):
            job = TransitionJob.objects.get(pk=job_id)
            async_order.refresh_from_db()
            self.assertEqual(job.status, JobStatus.FROZEN)

        # unfreeze
        for job_id in job_ids:
            job = TransitionJob.objects.get(pk=job_id)
            job.unfreeze()

        for job_id, async_order in zip(job_ids, async_orders):
            job = TransitionJob.objects.get(pk=job_id)
            async_order.refresh_from_db()
            self.assertEqual(job.status, JobStatus.FINISHED)
            self.assertEqual(async_order.counter, 2)
            self.assertEqual(async_order.name, 'def')
            # check if shared params and history kwargs are properly stored
            # during freezing
            self.assertEqual(
                job.params['shared_params'][async_order.pk]['test'], 'freezing'
            )
            # check history entries
            th = TransitionsHistory.objects.get(object_id=async_order.id)
            self.assertCountEqual(
                th.actions,
                [
                    "Assign user",
                    "Long running action",
                    "Freezing action"
                ]
            )

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
            requester=self.user,
            field='status',
            data={'name': 'def', 'foo': self.foo}
        )
        for job_id, order in zip(job_ids, [async_order, async_order2]):
            job = TransitionJob.objects.get(pk=job_id)
            self.assertEqual(job.status, JobStatus.FAILED.id)
            self.assertEqual(
                job.params['shared_params'][order.pk]['test'],
                'failing'
            )
            with self.assertRaises(TransitionsHistory.DoesNotExist):
                TransitionsHistory.objects.get(object_id=async_order.id)
