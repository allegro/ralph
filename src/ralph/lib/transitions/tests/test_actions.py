# -*- coding: utf-8 -*-
from dj.choices import Country
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient

from ralph.accounts.tests.factories import UserFactory
from ralph.assets.models.base import BaseObject
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.back_office.tests.factories import (
    BackOfficeAssetFactory,
    OfficeInfrastructureFactory,
    WarehouseFactory
)
from ralph.lib.external_services.models import JobStatus
from ralph.lib.transitions.models import TransitionJob, TransitionsHistory
from ralph.lib.transitions.tests import (
    TransitionTestCase,
    TransitionTestCaseMixin
)
from ralph.licences.tests.factories import LicenceFactory


class TransitionActionTestMixin(object):
    def setUp(self):
        super().setUp()
        self.warehouse_1 = WarehouseFactory(name='api_test')
        self.user = UserFactory()
        self.officeinfrastructure = OfficeInfrastructureFactory()
        self.bo = BackOfficeAssetFactory(
            status=BackOfficeAssetStatus.new,
            user=UserFactory(),
            owner=UserFactory()
        )
        self.licence_1 = LicenceFactory()
        self.licence_2 = LicenceFactory()
        actions = [
            'assign_user', 'assign_licence', 'assign_owner',
            'assign_loan_end_date', 'assign_warehouse',
            'assign_office_infrastructure', 'add_remarks', 'assign_task_url',
            'change_hostname'
        ]
        self.transition_1 = self._create_transition(
            BackOfficeAsset, 'BackOffice', actions, 'status',
            [BackOfficeAssetStatus.new.id],
            BackOfficeAssetStatus.in_progress.id
        )[1]
        self.transition_2 = self._create_transition(
            BackOfficeAsset, 'BackOffice_Async', actions, 'status',
            [BackOfficeAssetStatus.new.id],
            BackOfficeAssetStatus.in_progress.id,
            run_asynchronously=True
        )[1]
        self.superuser = get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.api_client = APIClient()
        self.api_client.login(username='test', password='test')

        self.client = Client()
        self.client.login(username='test', password='test')

    def prepare_gui_data(self):
        return {
            'add_remarks__remarks': 'remarks',
            'assign_owner__owner': self.user.id,
            'assign_loan_end_date__loan_end_date': '2016-04-01',
            'assign_task_url__task_url': 'http://test.allegro.pl',
            'assign_user__user': self.user.id,
            'assign_office_infrastructure__office_infrastructure':
            self.officeinfrastructure.id,
            'assign_warehouse__warehouse': self.warehouse_1.id,
            'change_hostname__country': Country.pl.id,
            'assign_licence__licences': [self.licence_1.id, self.licence_2.id]
        }

    def prepare_api_data(self):
        return {
            'remarks': 'remarks',
            'owner': self.user.id,
            'loan_end_date': '2016-04-01',
            'task_url': 'http://test.allegro.pl',
            'user': self.user.id,
            'office_infrastructure': self.officeinfrastructure.id,
            'warehouse': self.warehouse_1.id,
            'country': Country.pl.id,
            'licences': [self.licence_1.id, self.licence_2.id]
        }

    def get_transition_history(self, object_id):
        return TransitionsHistory.objects.filter(
            content_type=ContentType.objects.get_for_model(BaseObject),
            object_id=object_id
        ).last()


class TransitionActionTest(TransitionActionTestMixin, TransitionTestCase):
    def test_sync_api(self):
        response = self.api_client.post(
            reverse(
                'transitions-view',
                args=(self.transition_1.id, self.bo.pk)
            ),
            self.prepare_api_data()
        )
        self.assertEqual(response.status_code, 201)
        bo = BackOfficeAsset.objects.get(pk=self.bo)
        self.assertEqual(bo.owner_id, self.user.id)
        self.assertEqual(bo.warehouse_id, self.warehouse_1.id)
        history = self.get_transition_history(bo.pk)
        self.assertIn(self.user.username, history.kwargs['user'])

    def test_sync_api_validation_error(self):
        data = self.prepare_api_data()
        data['user'] = ''
        response = self.api_client.post(
            reverse(
                'transitions-view',
                args=(self.transition_1.id, self.bo.pk)
            ),
            data
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['user'],
            ['This field may not be blank.']
        )

    def test_sync_gui(self):
        request = self.client.post(
            reverse(
                'admin:back_office_backofficeasset_transition',
                args=(self.bo.id, self.transition_1.id)
            ),
            self.prepare_gui_data(),
            follow=True
        )
        self.assertTrue(
            request.redirect_chain[0][0],
            reverse(
                'admin:back_office_backofficeasset_change',
                args=(self.bo.id,)
            )
        )
        bo = BackOfficeAsset.objects.get(pk=self.bo)
        self.assertEqual(bo.owner_id, self.user.id)
        self.assertEqual(bo.warehouse_id, self.warehouse_1.id)
        history = self.get_transition_history(bo.pk)
        self.assertIn(self.user.username, history.kwargs['user'])

    def test_sync_gui_validation_error(self):
        data = self.prepare_gui_data()
        data['assign_warehouse__warehouse'] = ''
        request = self.client.post(
            reverse(
                'admin:back_office_backofficeasset_transition',
                args=(self.bo.id, self.transition_1.id)
            ),
            data,
            follow=True
        )
        self.assertEqual(
            request.context['form'].errors['assign_warehouse__warehouse'],
            ['This field is required.']
        )

    def test_api_options(self):
        request = self.api_client.options(
            reverse(
                'transition-view',
                args=(self.transition_1.id, self.bo.pk)
            )
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            request.data['actions']['POST'][
                'remarks'
            ]['type'], 'string'
        )
        self.assertEqual(
            request.data['actions']['POST'][
                'loan_end_date'
            ]['type'], 'date'
        )
        self.assertEqual(
            request.data['actions']['POST'][
                'country'
            ]['type'], 'choice'
        )


class TestAsyncActions(
    TransitionActionTestMixin,
    TransitionTestCaseMixin,
    TransactionTestCase
):
    def test_async_api(self):
        response = self.api_client.post(
            reverse(
                'transitions-view',
                args=(self.transition_2.id, self.bo.pk)
            ),
            self.prepare_api_data()
        )
        self.assertEqual(response.status_code, 202)
        bo = BackOfficeAsset.objects.get(pk=self.bo)
        self.assertEqual(bo.owner_id, self.user.id)
        self.assertEqual(bo.warehouse_id, self.warehouse_1.id)
        history = self.get_transition_history(bo.pk)
        self.assertIn(self.user.username, history.kwargs['user'])

    def test_async_gui(self):
        request = self.client.post(
            reverse(
                'admin:back_office_backofficeasset_transition',
                args=(self.bo.id, self.transition_2.id)
            ),
            self.prepare_gui_data(),
            follow=True
        )
        self.assertTrue(
            request.redirect_chain[0][0],
            reverse(
                'admin:back_office_backofficeasset_change',
                args=(self.bo.id,)
            )
        )
        bo = BackOfficeAsset.objects.get(pk=self.bo)
        self.assertEqual(bo.owner_id, self.user.id)
        self.assertEqual(bo.warehouse_id, self.warehouse_1.id)
        history = self.get_transition_history(bo.pk)
        self.assertIn(self.user.username, history.kwargs['user'])

    def test_async_gui_running_new_when_another_in_progress_should_return_error(self):  # noqa
        # mock another async job running
        TransitionJob.objects.create(
            obj=self.bo,
            transition=self.transition_2,
            status=JobStatus.STARTED,
            service_name='ASYNC',
        )
        request = self.client.post(
            reverse(
                'admin:back_office_backofficeasset_transition',
                args=(self.bo.id, self.transition_2.id)
            ),
            self.prepare_gui_data(),
            follow=True
        )
        self.assertTrue(
            request.redirect_chain[0][0],
            reverse(
                'admin:back_office_backofficeasset_change',
                args=(self.bo.id,)
            )
        )
        self.assertIn(
            'Another async transition for this object is already started',
            str(list(request.context['messages'])[1])
        )

    def test_async_api_running_new_when_another_in_progress_should_return_error(self):  # noqa
        # mock another async job running
        TransitionJob.objects.create(
            obj=self.bo,
            transition=self.transition_2,
            status=JobStatus.STARTED,
            service_name='ASYNC',
        )
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(self.transition_2.id, self.bo.pk)
            ),
            self.prepare_api_data()
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {
            'non_field_errors': [
                'Another async transition for this object is already started'
            ]
        })
