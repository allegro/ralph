from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import Client
from rest_framework.test import APIClient

from ralph.assets.models import AssetLastHostname
from ralph.data_center.models import DataCenterAsset
from ralph.data_center.tests.factories import (
    DataCenterAssetFactory,
    RackFactory
)
from ralph.lib.transitions.conf import TRANSITION_ORIGINAL_STATUS
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.networks.tests.factories import (
    NetworkEnvironmentFactory,
    NetworkFactory
)
from ralph.virtual.models import VirtualServer
from ralph.virtual.tests.factories import VirtualServerFactory


class _BaseDeploymentTransitionTestCase(object):
    model = None
    transition_url_name = None
    redirect_url_name = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hypervisor = DataCenterAssetFactory()
        cls.rack = RackFactory()
        cls.net_env = NetworkEnvironmentFactory(
            hostname_template_prefix='server_1',
            hostname_template_postfix='.mydc.net',
            hostname_template_counter_length=5,
        )
        cls.net_env_2 = NetworkEnvironmentFactory(
            hostname_template_prefix='server_2',
            hostname_template_postfix='.mydc2.net',
            hostname_template_counter_length=5,
        )
        cls.net_env_3 = NetworkEnvironmentFactory(
            hostname_template_prefix='server_3',
            hostname_template_postfix='.mydc3.net',
            hostname_template_counter_length=5,
        )
        cls.net = NetworkFactory(
            network_environment=cls.net_env,
            address='10.20.30.0/24',
        )
        cls.net_2 = NetworkFactory(
            network_environment=cls.net_env_2,
            address='11.20.30.0/24',
        )
        cls.net.racks.add(cls.rack)
        cls.net_2.racks.add(cls.rack)

    def setUp(self):
        super().setUp()

        self.superuser = get_user_model().objects.create_superuser(
            'test', 'test@test.test', 'test'
        )
        self.api_client = APIClient()
        self.api_client.force_authenticate(self.superuser)

        self.gui_client = Client()
        self.gui_client.login(username='test', password='test')

        AssetLastHostname.objects.create(
            prefix=self.net_env.hostname_template_prefix,
            postfix=self.net_env.hostname_template_postfix,
            counter=10,  # last used hostname was 10
        )

    def _prepare_assign_new_hostname_transition(self):
        actions = ['assign_new_hostname']
        self.assign_new_hostname_transition = self._create_transition(
            self.model, 'assign hostname', actions, 'status',
            source=list(dict(
                self.model._meta.get_field('status').choices
            ).keys()),
            target=str(TRANSITION_ORIGINAL_STATUS[0])
        )[1]

    def test_assign_new_hostname_through_api(self):
        self._prepare_assign_new_hostname_transition()
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(
                    self.assign_new_hostname_transition.id,
                    self.instance.pk
                )
            ),
            {'network_environment': self.net_env.pk}
        )
        self.assertEqual(response.status_code, 201)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_100011.mydc.net')
        # another request
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(
                    self.assign_new_hostname_transition.id,
                    self.instance.pk
                )
            ),
            {'network_environment': self.net_env.pk}
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_100012.mydc.net')

    def test_assign_new_hostname_through_api_without_asset_last_hostname(self):
        self._prepare_assign_new_hostname_transition()
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(
                    self.assign_new_hostname_transition.id,
                    self.instance.pk
                )
            ),
            {'network_environment': self.net_env_2.pk}
        )
        self.assertEqual(response.status_code, 201)
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_200001.mydc2.net')
        # another request
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(
                    self.assign_new_hostname_transition.id,
                    self.instance.pk
                )
            ),
            {'network_environment': self.net_env_2.pk}
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_200002.mydc2.net')

    def test_assign_new_hostname_through_api_wrong_network_env(self):
        self._prepare_assign_new_hostname_transition()
        response = self.api_client.post(
            reverse(
                'transition-view',
                args=(
                    self.assign_new_hostname_transition.id,
                    self.instance.pk
                )
            ),
            {'network_environment': self.net_env_3.pk}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('network_environment', response.data)
        self.assertIn(
            '"{}" is not a valid choice.'.format(self.net_env_3.pk),
            response.data['network_environment']
        )

    def test_assign_new_hostname_through_gui(self):
        self._prepare_assign_new_hostname_transition()
        response = self.gui_client.post(
            reverse(
                self.transition_url_name,
                args=(self.instance.id, self.assign_new_hostname_transition.id)
            ),
            {'assign_new_hostname__network_environment': self.net_env.pk},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.redirect_chain[0][0],
            reverse(self.redirect_url_name, args=(self.instance.id,))
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_100011.mydc.net')
        # another assignment
        self.gui_client.post(
            reverse(
                self.transition_url_name,
                args=(self.instance.id, self.assign_new_hostname_transition.id)
            ),
            {'assign_new_hostname__network_environment': self.net_env.pk},
            follow=True
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_100012.mydc.net')

    def test_assign_new_hostname_through_gui_without_asset_last_hostname(self):
        self._prepare_assign_new_hostname_transition()
        response = self.gui_client.post(
            reverse(
                self.transition_url_name,
                args=(self.instance.id, self.assign_new_hostname_transition.id)
            ),
            {'assign_new_hostname__network_environment': self.net_env_2.pk},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.redirect_chain[0][0],
            reverse(self.redirect_url_name, args=(self.instance.id,))
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_200001.mydc2.net')
        # another assignment
        self.gui_client.post(
            reverse(
                self.transition_url_name,
                args=(self.instance.id, self.assign_new_hostname_transition.id)
            ),
            {'assign_new_hostname__network_environment': self.net_env_2.pk},
            follow=True
        )
        self.instance.refresh_from_db()
        self.assertEqual(self.instance.hostname, 'server_200002.mydc2.net')

    def test_assign_new_hostname_through_gui_with_wrong_network_env(self):
        self._prepare_assign_new_hostname_transition()
        response = self.gui_client.post(
            reverse(
                self.transition_url_name,
                args=(self.instance.id, self.assign_new_hostname_transition.id)
            ),
            {'assign_new_hostname__network_environment': self.net_env_3.pk},
            # no following redirects here!
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'assign_new_hostname__network_environment',
            response.context_data['form'].errors
        )


class VirtualServerDeploymentTransitionTestCase(
    _BaseDeploymentTransitionTestCase, TransitionTestCase
):
    model = VirtualServer
    transition_url_name = 'admin:virtual_virtualserver_transition'
    redirect_url_name = 'admin:virtual_virtualserver_change'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent = DataCenterAssetFactory(
            rack=cls.rack,
        )

    def setUp(self):
        super().setUp()
        self.instance = VirtualServerFactory(parent=self.parent)


class DataCenterAssetDeploymentTransitionTestCase(
    _BaseDeploymentTransitionTestCase, TransitionTestCase
):
    model = DataCenterAsset
    transition_url_name = 'admin:data_center_datacenterasset_transition'
    redirect_url_name = 'admin:data_center_datacenterasset_change'

    def setUp(self):
        super().setUp()
        self.instance = DataCenterAssetFactory(rack=self.rack)
