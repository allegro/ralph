# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.scan.data import (
    check_if_can_edit_position,
    connection_from_data,
    device_from_data,
    get_choice_by_name,
    get_device_data,
    merge_data,
    set_device_data,
)
from ralph.scan.tests.samples.choices import SampleChoices
from ralph.discovery.models import (
    ComponentModel,
    ComponentType,
    Connection,
    ConnectionType,
    Device,
    DeviceModel,
    DeviceType,
    DiskShare,
    DiskShareMount,
    Ethernet,
    FibreChannel,
    GenericComponent,
    IPAddress,
    Memory,
    NetworkConnection,
    OperatingSystem,
    Processor,
    Software,
    Storage,
)
from ralph_assets.tests.utils.assets import DCAssetFactory


class GetDeviceDataTest(TestCase):

    def setUp(self):
        self.device_model = DeviceModel(
            type=DeviceType.rack_server, name="ziew-X")
        self.device_model.save()
        self.device = Device(
            model=self.device_model,
            sn='123456789',
            name='ziew',
        )
        self.device.save()

    def test_basic_data(self):
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['serial_number'], '123456789')
        self.assertEqual(data['hostname'], 'ziew')
        self.assertEqual(data['type'], 'rack server')
        self.assertEqual(data['model_name'], 'ziew-X')

    def test_position(self):
        self.device.chassis_position = 3
        self.device.dc = 'dc3'
        self.device.rack = '232'
        self.device.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['chassis_position'], 3)
        self.assertEqual(data['data_center'], 'dc3')
        self.assertEqual(data['rack'], '232')

    def test_memory(self):
        for i in xrange(8):
            m = Memory(
                label="ziew",
                size=128,
                device=self.device,
                index=i,
            )
            m.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        memory = data['memory']
        self.assertEqual(len(memory), 8)
        self.assertEqual(memory[0]['label'], "ziew")
        self.assertEqual(memory[0]['size'], 128)
        self.assertEqual(memory[3]['index'], 3)

    def test_processors(self):
        model = ComponentModel(
            type=ComponentType.processor,
            name="CPU Xeon 2533MHz, 4-core",
        )
        model.save()
        for i in xrange(4):
            p = Processor(
                label="ziew",
                model=model,
                device=self.device,
                index=i,
            )
            p.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        processors = data['processors']
        self.assertEqual(len(processors), 4)
        self.assertEqual(processors[0]['label'], "ziew")
        self.assertEqual(
            processors[0]['model_name'], "CPU Xeon 2533MHz, 4-core")
        self.assertEqual(processors[0]['cores'], 4)
        self.assertEqual(processors[3]['index'], 3)

    def test_disks(self):
        model = ComponentModel(
            type=ComponentType.disk,
            name="HP DG0300BALVP SAS 307200MiB, 10000RPM",
        )
        model.save()
        Storage(
            sn="abc3",
            device=self.device,
            label="ziew",
            mount_point="/dev/hda",
            model=model,
            size=307200,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        disks = data['disks']
        self.assertEqual(len(disks), 1)
        self.assertEqual(disks[0]['size'], 307200)
        self.assertEqual(disks[0]['serial_number'], "abc3")
        self.assertEqual(disks[0]['mount_point'], "/dev/hda")

    def test_fc(self):
        model = ComponentModel(
            type=ComponentType.fibre,
            name="FC-336",
        )
        model.save()
        FibreChannel(
            physical_id='deadbeefcafe',
            label='ziew',
            device=self.device,
            model=model,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        fc = data['fibrechannel_cards']
        self.assertEqual(len(fc), 1)
        self.assertEqual(fc[0]['physical_id'], 'deadbeefcafe')
        self.assertEqual(fc[0]['model_name'], 'FC-336')

    def test_mac_addresses(self):
        for i in xrange(5):
            mac = 'deadbeefcaf%d' % i
            Ethernet(mac=mac, device=self.device).save()

    def test_parts(self):
        model = ComponentModel(
            type=ComponentType.management,
            name="weapons of mass destruction",
        )
        model.save()
        GenericComponent(
            label='ziew',
            device=self.device,
            model=model,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        parts = data['parts']
        self.assertEqual(parts[0]['type'], "management")
        self.assertEqual(parts[0]['model_name'], "weapons of mass destruction")
        self.assertEqual(len(parts), 1)

    def test_software(self):
        model = ComponentModel(
            type=ComponentType.software,
            name="cobol",
        )
        model.save()
        Software(
            label='cobol',
            device=self.device,
            model=model,
            version='1.0.0',
            path='/usr/bin/cobol',
            sn='0000001',
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        soft = data['installed_software']
        self.assertEqual(soft[0]['version'], "1.0.0")
        self.assertEqual(soft[0]['model_name'], "cobol")
        self.assertEqual(len(soft), 1)

    def test_disk_shares_and_exports(self):
        model = ComponentModel(
            type=ComponentType.share,
            name="3par share",
        )
        model.save()
        share = DiskShare(
            device=self.device,
            model=model,
            label="pr0n",
            size="2048",
            wwn="deadbeefcafe1234",
        )
        share.save()
        address = IPAddress(address='127.0.0.1')
        address.save()
        DiskShareMount(
            device=self.device,
            share=share,
            address=address,
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        exports = data['disk_exports']
        mounts = data['disk_shares']
        self.assertEqual(len(exports), 1)
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0]['serial_number'], "deadbeefcafe1234")

    def test_system(self):
        OperatingSystem.create(
            self.device,
            "Haiku",
            0,
            version="1.0.0",
            memory='512',
            storage='2048',
            cores_count='4',
            family="BeOS",
        )
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['system_memory'], 512)
        self.assertEqual(data['system_storage'], 2048)
        self.assertEqual(data['system_cores_count'], 4)
        self.assertEqual(data['system_family'], "BeOS")
        self.assertEqual(data['system_label'], "Haiku 1.0.0")

    def test_subdevices(self):
        Device(
            parent=self.device,
            model=self.device_model,
            sn='1',
            name='ziew1',
        ).save()
        Device(
            parent=self.device,
            model=self.device_model,
            sn='2',
            name='ziew2',
        ).save()
        Device(
            parent=self.device,
            model=self.device_model,
            sn='3',
            name='ziew3',
        ).save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        sub = data['subdevices']
        self.assertEqual(len(sub), 3)

    def test_management(self):
        self.device.management = IPAddress.objects.create(address='10.10.10.1')
        self.device.save()
        data = get_device_data(Device.objects.get(sn='123456789'))
        self.assertEqual(data['management'], '10.10.10.1')

    def test_connections(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        IPAddress.objects.create(
            address="10.0.22.1",
            device=connected_device_1
        )
        connection = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_1
        )
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        IPAddress.objects.create(
            address="10.0.22.2",
            device=connected_device_2
        )
        IPAddress.objects.create(
            address="10.0.22.3",
            device=connected_device_2
        )
        connection = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_2
        )
        NetworkConnection.objects.create(
            connection=connection,
            outbound_port="eth0",
            inbound_port="eth1"
        )
        data = get_device_data(Device.objects.get(sn='sn_1'))
        self.assertEqual(
            data['connections'],
            [
                {
                    'connected_device_ip_addresses': '10.0.22.1',
                    'connected_device_mac_addresses': '',
                    'connected_device_serial_number': 'sn_2',
                    'connection_details': {},
                    'connection_type': 'network'
                },
                {
                    'connected_device_ip_addresses': '10.0.22.2,10.0.22.3',
                    'connected_device_mac_addresses': '',
                    'connected_device_serial_number': 'sn_3',
                    'connection_details': {
                        'inbound_port': 'eth1',
                        'outbound_port': 'eth0'
                    },
                    'connection_type': 'network'
                }
            ]
        )


class SetDeviceDataTest(TestCase):

    def setUp(self):
        self.device_model = DeviceModel(
            type=DeviceType.rack_server,
            name="ziew-X",
        )
        self.device_model.save()
        self.device = Device(
            model=self.device_model,
            sn='123456789',
            name='ziew',
        )
        self.device.save()

    def test_basic_data(self):
        data = {
            'serial_number': 'aaa123456789',
            'hostname': 'mervin',
            'data_center': 'chicago',
            'barcode': '00000',
            'rack': 'i31',
            'chassis_position': '4',
            'management': '10.10.10.2'
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='aaa123456789')
        self.assertEqual(device.sn, 'aaa123456789')
        self.assertEqual(device.name, 'mervin')
        self.assertEqual(device.dc, 'chicago')
        self.assertEqual(device.barcode, '00000')
        self.assertEqual(device.rack, 'i31')
        self.assertEqual(device.chassis_position, 4)
        self.assertEqual(device.management.address, '10.10.10.2')

    def test_basic_data_with_asset(self):
        asset = DCAssetFactory()
        asset.model.category.is_blade = False
        asset.model.category.save()
        data = {
            'serial_number': 'aaa123456789',
            'hostname': 'mervin',
            'data_center': 'chicago',
            'barcode': '00000',
            'rack': 'i31',
            'chassis_position': '4',
            'management': '10.10.10.2',
            'asset': asset,
        }
        warnings = []
        set_device_data(self.device, data, warnings=warnings)
        self.device.save()
        device = Device.objects.get(sn='aaa123456789')
        self.assertIsNone(device.dc)
        self.assertIsNone(device.rack)
        self.assertIsNone(device.chassis_position)
        self.assertIsNone(device.management)
        self.assertEqual(
            warnings,
            [
                'You can not set data for `chassis_position` here - skipped. '
                'Use assets module.',
                'You can not set data for `data_center` here - skipped. '
                'Use assets module.',
                'You can not set data for `rack` here - skipped. '
                'Use assets module.',
                'Management IP address (10.10.10.2) has been ignored. To '
                'change them, please use the Assets module.',
            ]
        )

    def test_model_name(self):
        data = {
            'type': 'blade_server',
            'model_name': 'ziew-Y',
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        self.assertEqual(device.model.name, 'ziew-Y')
        self.assertEqual(device.model.type, DeviceType.blade_server)
        data = {
            'type': 'rack_server',
            'model_name': 'ziew-X',
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        self.assertEqual(device.model.name, 'ziew-X')
        self.assertEqual(device.model.type, DeviceType.rack_server)

    def test_disks(self):
        data = {
            'disks': [
                {
                    'serial_number': '1234',
                    'size': '128',
                    'mount_point': '/dev/sda',
                    'label': 'sda',
                    'family': 'Simpsons',
                },
                {
                    'size': '512',
                    'mount_point': '/dev/sdb',
                    'label': 'sdb',
                    'family': 'Jetsons',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        disks = list(device.storage_set.order_by('label'))
        self.assertEqual(disks[0].mount_point, '/dev/sda')
        self.assertEqual(disks[0].sn, '1234')
        self.assertEqual(disks[0].model.family, 'Simpsons')
        self.assertEqual(disks[1].sn, None)
        self.assertEqual(disks[1].mount_point, '/dev/sdb')
        self.assertEqual(disks[1].model.family, 'Jetsons')
        self.assertEqual(len(disks), 2)
        data = {
            'disks': [
                {
                    'mount_point': '/dev/sda',
                    'family': 'Simpsons',
                },
                {
                    'serial_number': '12346',
                    'mount_point': '/dev/sdb',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        disks = list(device.storage_set.order_by('label'))
        self.assertEqual(disks[0].mount_point, '/dev/sda')
        self.assertEqual(disks[0].sn, '1234')
        self.assertEqual(disks[0].model.family, 'Simpsons')
        self.assertEqual(disks[1].sn, '12346')
        self.assertEqual(disks[1].mount_point, '/dev/sdb')
        self.assertEqual(disks[1].model.family, 'Jetsons')
        self.assertEqual(len(disks), 2)
        data = {
            'disks': [
                {
                    'mount_point': '/dev/sda',
                    'family': 'Simpsons',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        disks = list(device.storage_set.order_by('label'))
        self.assertEqual(disks[0].mount_point, '/dev/sda')
        self.assertEqual(disks[0].sn, '1234')
        self.assertEqual(disks[0].model.family, 'Simpsons')
        self.assertEqual(len(disks), 1)

    def test_memory(self):
        data = {
            'memory': [
                {
                    'size': '128',
                },
                {
                    'size': '128',
                },
                {
                    'size': '128',
                },
                {
                    'size': '128',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        memory = list(device.memory_set.order_by('index'))
        self.assertEqual(memory[0].size, 128)
        self.assertEqual(memory[0].index, 0)
        self.assertEqual(len(memory), 4)
        data = {
            'memory': [
                {
                    'size': '256',
                },
                {
                    'size': '256',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        memory = list(device.memory_set.order_by('index'))
        self.assertEqual(memory[0].size, 256)
        self.assertEqual(memory[0].index, 0)
        self.assertEqual(len(memory), 2)

    def test_processors(self):
        data = {
            'processors': [
                {
                    'model_name': 'CPU Xeon 2533MHz, 4-core',
                    'family': 'Xeon',
                    'cores': '4',
                    'speed': '2533',
                },
                {
                    'model_name': 'CPU Xeon 2533MHz, 4-core',
                    'family': 'Xeon',
                    'speed': '2533',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        processors = list(device.processor_set.order_by('index'))
        self.assertEqual(processors[0].model.name, 'CPU Xeon 2533MHz, 4-core')
        self.assertEqual(processors[0].model.type, ComponentType.processor)
        self.assertEqual(processors[0].cores, 4)
        self.assertEqual(processors[0].speed, 2533)
        self.assertEqual(len(processors), 2)

    def test_mac_addresses(self):
        data = {
            'mac_addresses': [
                'deadbeefcaf0',
                'deadbeefcaf1',
                'deadbeefcaf2',
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        ethernets = list(device.ethernet_set.order_by('label', 'mac'))
        self.assertEqual(len(ethernets), 3)
        self.assertEqual(ethernets[2].mac, 'DEADBEEFCAF2')
        data = {
            'mac_addresses': [
                'deadbeefcaf0',
                'deadbeefcaf1',
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        ethernets = list(device.ethernet_set.order_by('label', 'mac'))
        self.assertEqual(len(ethernets), 2)
        self.assertEqual(ethernets[1].mac, 'DEADBEEFCAF1')

    def test_ip_addresses(self):
        data = {
            'system_ip_addresses': [
                '127.0.0.1',
                '127.0.0.2',
            ],
            'management_ip_addresses': [
                '127.0.0.3',
                '127.0.0.4',
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        system_addresses = list(
            device.ipaddress_set.filter(is_management=False).order_by('number')
        )
        management_addresses = list(
            device.ipaddress_set.filter(is_management=True).order_by('number')
        )
        self.assertEqual(len(system_addresses), 2)
        self.assertEqual(len(management_addresses), 2)
        self.assertEqual(system_addresses[0].is_management, False)
        self.assertEqual(management_addresses[0].is_management, True)
        self.assertEqual(system_addresses[0].address, '127.0.0.1')
        self.assertEqual(management_addresses[0].address, '127.0.0.3')
        data = {
            'system_ip_addresses': [
                '127.0.0.1',
            ],
            'management_ip_addresses': [
                '127.0.0.2',
                '127.0.0.3',
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        system_addresses = list(
            device.ipaddress_set.filter(is_management=False).order_by('number')
        )
        management_addresses = list(
            device.ipaddress_set.filter(is_management=True).order_by('number')
        )
        self.assertEqual(len(system_addresses), 1)
        self.assertEqual(len(management_addresses), 2)
        address = IPAddress.objects.get(address='127.0.0.4')
        self.assertEqual(address.device, None)

    def test_device_with_asset_ip_addresses(self):
        asset = DCAssetFactory()
        data = {
            'system_ip_addresses': [
                '127.0.0.1',
                '127.0.0.2',
            ],
            'management_ip_addresses': [
                '127.0.0.3',
                '127.0.0.4',
            ],
            'asset': asset,
        }
        warnings = []
        set_device_data(self.device, data, warnings=warnings)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        self.assertEqual(
            device.ipaddress_set.filter(is_management=False).count(), 2,
        )
        self.assertEqual(
            device.ipaddress_set.filter(is_management=True).count(), 0,
        )
        self.assertEqual(
            warnings,
            [
                'Management IP addresses (127.0.0.3, 127.0.0.4) have been '
                'ignored. To change them, please use the Assets module.',
            ],
        )

    def test_fc(self):
        data = {
            'fibrechannel_cards': [
                {
                    'physical_id': "deadbeefcafe",
                    'label': "ziew",
                    'model_name': "FC-1000",
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        fc = device.fibrechannel_set.get()
        self.assertEqual(fc.physical_id, "deadbeefcafe")
        self.assertEqual(fc.label, "ziew")
        self.assertEqual(fc.model.name, "FC-1000")
        self.assertEqual(fc.model.type, ComponentType.fibre)

    def test_parts(self):
        data = {
            'parts': [
                {
                    'serial_number': "abc123",
                    'type': 'management',
                    'label': "Terminator management",
                    'model_name': "T-500 management module",
                    'hard_firmware': "T-500-1",
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        part = device.genericcomponent_set.get()
        self.assertEqual(part.label, "Terminator management")
        self.assertEqual(part.model.name, "T-500 management module")
        self.assertEqual(part.model.type, ComponentType.management)
        self.assertEqual(part.sn, "abc123")

    def test_disk_exports_and_shares(self):
        data = {
            'disk_exports': [
                {
                    'serial_number': "deadbeefcafe1234",
                    'size': '2048',
                    'label': 'pr0n',
                },
            ],
            'disk_shares': [
                {
                    'serial_number': "deadbeefcafe1234",
                    'server': {
                        'device': {
                            'serial_number': '123456789',
                        },
                    },
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        export = device.diskshare_set.get()
        mount = device.disksharemount_set.get()
        self.assertEqual(export.label, "pr0n")
        self.assertEqual(export.size, 2048)
        self.assertEqual(export.wwn, "deadbeefcafe1234")
        self.assertEqual(mount.share, export)
        self.assertEqual(mount.server, device)

    def test_software(self):
        data = {
            'installed_software': [
                {
                    'label': 'Doom 2',
                    'version': '2',
                    'path': '/usr/local/games/bin/doom',
                    'model_name': 'Doom',
                    'serial_number': 'Blooood!',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        soft = device.software_set.get()
        self.assertEqual(soft.label, "Doom 2")
        self.assertEqual(soft.version, "2")
        self.assertEqual(soft.model.name, "Doom")
        self.assertEqual(soft.model.type, ComponentType.software)

    def test_system(self):
        data = {
            'system_label': 'Haiku 1.0.0',
            'system_memory': '512',
            'system_storage': '2048',
            'system_cores_count': 4,
            'system_family': 'BeOS',
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        system = device.operatingsystem_set.get()
        self.assertEqual(system.label, "Haiku 1.0.0")
        self.assertEqual(system.memory, 512)
        self.assertEqual(system.storage, 2048)
        self.assertEqual(system.cores_count, 4)
        self.assertEqual(system.model.name, "BeOS")
        self.assertEqual(system.model.family, "BeOS")
        self.assertEqual(system.model.type, ComponentType.os)

    def test_subdevices(self):
        data = {
            'subdevices': [
                {
                    'serial_number': '1',
                    'type': 'virtual_server',
                    'hostname': 'ziew1',
                    'model_name': 'XEN Virtual Server',
                },
                {
                    'mac_addresses': ['beefcafedead'],
                    'type': 'virtual_server',
                    'hostname': 'ziew2',
                    'model_name': 'XEN Virtual Server',
                },
            ],
        }
        set_device_data(self.device, data)
        self.device.save()
        device = Device.objects.get(sn='123456789')
        subdevices = list(device.child_set.order_by('name'))
        self.assertEqual(len(subdevices), 2)
        self.assertEqual(subdevices[0].name, 'ziew1')
        self.assertEqual(subdevices[1].name, 'ziew2')

    def test_connections(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        Ethernet.objects.create(mac='112233AABBDD', device=connected_device_1)
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        Ethernet.objects.create(mac='112233AABBEE', device=connected_device_2)
        data = {
            'connections': [
                {
                    'connected_device_mac_addresses': '112233AABBDD',
                    'connection_type': 'network'
                },
                {
                    'connected_device_mac_addresses': '112233AABBEE',
                    'connection_type': 'network',
                    'details': {
                        'outbound_port': 'eth1',
                        'inbound_port': 'gr2'
                    }
                }
            ]
        }
        set_device_data(master_device, data)
        master_device.save()
        device = Device.objects.get(sn='sn_1')
        connections = device.outbound_connections.all()
        self.assertEqual(connections[0].inbound.id, connected_device_1.id)
        self.assertEqual(connections[1].inbound.id, connected_device_2.id)
        self.assertEqual(
            connections[1].networkconnection.outbound_port,
            "eth1"
        )
        self.assertEqual(
            connections[1].networkconnection.inbound_port,
            "gr2"
        )

    def test_check_if_can_edit_position(self):
        # No asset in saved data.
        self.assertTrue(check_if_can_edit_position({'key_1': 'value_1'}))
        # Asset is assigned.
        asset = DCAssetFactory()
        self.assertFalse(
            check_if_can_edit_position({'key_1': 'value_1', 'asset': asset}),
        )
        # Asset string representation - asset does not exist.
        self.assertTrue(
            check_if_can_edit_position(
                {'key_1': 'value_1', 'asset': 'Name - SN - BARCODE'},
            ),
        )


class DeviceFromDataTest(TestCase):

    def test_device_from_data(self):
        device = device_from_data({
            'serial_number': "12345",
            'model_name': "ziew-X",
        })
        self.assertEqual(device.sn, '12345')
        self.assertEqual(device.model.name, "ziew-X")
        self.assertEqual(device.model.type, DeviceType.unknown)


class DeviceMergeDataTest(TestCase):

    def test_basic_data(self):
        data = [
            {
                'one': {
                    'device': {
                        'key1': 'value1',
                        'key2': 'value2',
                    },
                },
                'two': {
                    'device': {
                        'key1': 'value1',
                        'key2': 'value2',
                    },
                },
                'database': {
                    'device': {
                        'key2': 'value2',
                    },
                },
            },
            {
                'three': {
                    'device': {
                        'key1': 'value2',
                        'key3': 'value3',
                    },
                },
            },
        ]
        merged = merge_data(*data)
        self.assertEqual(merged, {
            'key1': {
                ('one', 'two'): 'value1',
                ('three',): 'value2',
            },
            'key2': {
                ('database', 'one', 'two'): 'value2',
            },
            'key3': {
                ('three',): 'value3',
            },
        })
        merged = merge_data(*data, only_multiple=True)
        self.assertEqual(merged, {
            'key1': {
                ('one', 'two'): 'value1',
                ('three',): 'value2',
            },
            'key3': {
                ('three',): 'value3',
            },
        })


class GetChoiceByNameTest(TestCase):

    def test_find_item_by_name(self):
        choice = get_choice_by_name(SampleChoices, 'simple')
        self.assertEqual(choice.id, 1)
        self.assertEqual(choice.name, 'simple')
        self.assertEqual(choice.raw, 'simple')
        choice = get_choice_by_name(SampleChoices, 'not_simple')
        self.assertEqual(choice.id, 2)
        self.assertEqual(choice.name, 'not_simple')
        self.assertEqual(choice.raw, 'not simple')

    def test_find_item_by_name_with_spaces(self):
        choice = get_choice_by_name(SampleChoices, 'Not Simple')
        self.assertEqual(choice.id, 2)
        self.assertEqual(choice.name, 'not_simple')
        self.assertEqual(choice.raw, 'not simple')

    def test_find_item_by_raw_name(self):
        choice = get_choice_by_name(SampleChoices, 'some difficult case')
        self.assertEqual(choice.id, 3)
        self.assertEqual(choice.name, 'difficult')
        self.assertEqual(choice.raw, 'some difficult case')

    def test_not_found(self):
        self.assertRaises(
            ValueError,
            get_choice_by_name,
            SampleChoices,
            'abc'
        )


class ConnectionFromData(TestCase):

    def test_return_existing_connection(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        connected_device_3 = Device.objects.create(
            model=model,
            sn='sn_4',
            name='dev4.dc1'
        )
        connected_device_4 = Device.objects.create(
            model=model,
            sn='sn_5',
            name='dev5.dc1'
        )
        Ethernet.objects.create(mac='112233AABBCC', device=connected_device_2)
        Ethernet.objects.create(mac='112233AABBDD', device=connected_device_4)
        IPAddress.objects.create(
            address='10.20.30.1',
            device=connected_device_3
        )
        IPAddress.objects.create(
            address='10.20.30.2',
            device=connected_device_4
        )
        connection_1 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_1
        )
        connection_2 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_2
        )
        connection_3 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_3
        )
        connection_4 = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device_4
        )
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': 'sn_2',
                'connected_device_mac_addresses': '',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.id, connection_1.id)
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_1.id)
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': '',
                'connected_device_mac_addresses': '112233AABBCC',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.id, connection_2.id)
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_2.id)
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': '',
                'connected_device_ip_addresses': '10.20.30.1',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.id, connection_3.id)
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_3.id)
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': 'sn_5',
                'connected_device_mac_addresses': '112233AABBDD',
                'connected_device_ip_addresses': '10.20.30.2',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.id, connection_4.id)
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_4.id)

    def test_return_new_connection(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        Ethernet.objects.create(mac='112233AABBCC', device=connected_device_2)
        IPAddress.objects.create(
            address='10.20.30.2',
            device=connected_device_2
        )
        IPAddress.objects.create(
            address='10.20.30.3',
            device=connected_device_2
        )
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': 'sn_2',
                'connected_device_mac_addresses': '',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_1.id)
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': '',
                'connected_device_mac_addresses': '112233AABBCC',
                'connected_device_ip_addresses': '10.20.30.2,10.20.30.3',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.outbound.id, master_device.id)
        self.assertEqual(connection.inbound.id, connected_device_2.id)

    def test_connection_details(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        Ethernet.objects.create(mac='112233AABBDD', device=connected_device)
        connection = Connection.objects.create(
            connection_type=ConnectionType.network,
            outbound=master_device,
            inbound=connected_device
        )
        NetworkConnection.objects.create(
            connection=connection,
            outbound_port="eth0",
            inbound_port="eth1"
        )
        connection = connection_from_data(
            master_device,
            {
                'connected_device_serial_number': 'sn_2',
                'connected_device_mac_addresses': '112233AABBDD',
                'connection_type': 'network connection'
            }
        )
        self.assertEqual(connection.networkconnection.outbound_port, "eth0")
        self.assertEqual(connection.networkconnection.inbound_port, "eth1")

    def test_incorrect_input(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        self.assertRaises(
            ValueError,
            connection_from_data,
            master_device,
            {
                'connection_type': 'network connection'
            }
        )
        self.assertRaises(
            ValueError,
            connection_from_data,
            master_device,
            {
                'connected_device_mac_addresses': '112233AABBDD',
                'connection_type': 'network connection'
            }
        )

    def test_incorrect_data_in_db(self):
        model = DeviceModel.objects.create(
            type=DeviceType.rack_server,
            name="DevModel F1"
        )
        master_device = Device.objects.create(
            model=model,
            sn='sn_1',
            name='dev1.dc1'
        )
        connected_device_1 = Device.objects.create(
            model=model,
            sn='sn_2',
            name='dev2.dc1'
        )
        Ethernet.objects.create(mac='112233AABBDD', device=connected_device_1)
        connected_device_2 = Device.objects.create(
            model=model,
            sn='sn_3',
            name='dev3.dc1'
        )
        Ethernet.objects.create(mac='112233AABBEE', device=connected_device_2)
        connected_device_3 = Device.objects.create(
            model=model,
            sn='sn_4',
            name='dev4.dc1'
        )
        IPAddress.objects.create(
            address='10.10.0.10',
            device=connected_device_3
        )
        self.assertRaises(
            ValueError,
            connection_from_data,
            master_device,
            {
                'connected_device_mac_addresses': '112233AABBDD,112233AABBEE',
                'connection_type': 'network connection'
            }
        )
        self.assertRaises(
            ValueError,
            connection_from_data,
            master_device,
            {
                'connected_device_mac_addresses': '112233AABBDD',
                'connected_device_ip_addresses': '10.10.0.10',
                'connection_type': 'network connection'
            }
        )
