# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase
from lck.django.common.models import MACAddressField

from ralph.cmdb.tests.utils import (
    DeviceEnvironmentFactory,
    ServiceCatalogFactory,
)
from ralph.dnsedit.tests.util import DNSRecordFactory, DNSDomainFactory
from ralph.deployment.tests.utils import PrebootFactory, DeploymentFactory
from ralph.deployment.models import MassDeployment, Deployment
from ralph.discovery.models import DeviceType
from ralph.discovery.tests.util import (
    DeviceFactory,
    EthernetFactory,
    NetworkFactory,
    DeviceFactory,
    DeviceModelFactory,
    IPAddressFactory,
)
from ralph.ui.tests.global_utils import login_as_su
from ralph.util.tests.utils import VentureRoleFactory


class MassDeploymentTest(TestCase):

    def setUp(self):
        self.client = login_as_su()
        self.device_environment = DeviceEnvironmentFactory(name='testenv')
        self.service = ServiceCatalogFactory(name='testservice')
        self.preboot = PrebootFactory(name="prebotname")
        self.ethernet = EthernetFactory.create(
            mac="0025b0000000",
        )
        self.network = NetworkFactory.create(
            address='10.80.80.0/20',
            name='testnetwork',
        )
        self.network.save()
        self.venture_role = VentureRoleFactory(
            name="testventurerole",
            venture__symbol='testventure',
            venture__name='testventure'
        )

    def _base_check_for_mass_deployment(
        self,
        response,
        csv_field_name,
        expected_csv,
    ):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MassDeployment.objects.count(), 1)
        self.assertEqual(
            getattr(MassDeployment.objects.all()[0], csv_field_name),
            expected_csv,
        )

    def test_prepare_mass_deployment(self):
        csv = (
            '{0}; 10.80.80.100; {1}; '
            '{2}; {3}; {4} ; {5} ; {6}'.format(
                self.ethernet.mac,
                self.network.name,
                self.venture_role.venture.symbol,
                self.venture_role.name,
                self.service.name,
                self.device_environment.name,
                self.preboot.name,
            )
        )
        response = self.client.post(reverse('prepare_mass_deploy'), {
            'csv': csv
        })

        self._base_check_for_mass_deployment(response, 'csv', csv)

    def test_mass_deployment(self):
        ip = '10.80.80.101'
        self.test_prepare_mass_deployment()
        ip_address = IPAddressFactory()
        device_model = DeviceModelFactory(
            type=DeviceType.rack,
            name="testrack",
        )
        device = DeviceFactory(
            name="testdevice",
            model=device_model,
            sn="testsn",
        )
        device.ipaddress.add(ip_address)
        ethernet = EthernetFactory.create(
            mac="0022b0000000",
            device=device,
        )
        self.network.racks.add(device)
        mass_deployment = MassDeployment.objects.all()[0]
        dns_domain = DNSDomainFactory(name='dc')
        dns_record = DNSRecordFactory(
            name='d001.dc',
            type='A',
            content=ip_address.address,
            domain=dns_domain,
        )
        url = reverse(
            'mass_deploy',
            kwargs={"deployment": mass_deployment.id},
        )
        csv = (
            '{0}; {1}; {2}; '
            '{3}; 10.80.80.102; {4}; {5} ; {6} ; {7} ; {8} ; {9}'.format(
                dns_record.name,
                ip,
                device.sn,
                ethernet.mac,
                self.network.name,
                self.venture_role.venture.symbol.upper(),
                self.venture_role.name,
                self.service.name,
                self.device_environment.name,
                self.preboot.name,
            )
        )
        response = self.client.post(url, {
            'csv': csv,
        })

        self._base_check_for_mass_deployment(response, 'generated_csv', csv)
        deployment = Deployment.objects.get(device=device)
        self.assertEqual(deployment.venture, self.venture_role.venture)
        self.assertEqual(deployment.venture_role, self.venture_role)
        self.assertEqual(deployment.service, self.service)
        self.assertEqual(
            deployment.device_environment,
            self.device_environment,
        )
        self.assertEqual(deployment.preboot, self.preboot)
        self.assertEqual(deployment.ip, ip)
        self.assertEqual(
            deployment.mac,
            MACAddressField.normalize(ethernet.mac),
        )
