# -*- coding: utf-8 -*-

VMWARE_SAMPLE = {
    'devices': {
        100: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [500, 12000, 7000, 1000, 4000],
            'key': 100,
            'label': 'PCI controller 0',
            'summary': 'PCI controller 0',
            'type': 'VirtualPCIController',
            'unitNumber': None
        },
        200: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [3000],
            'key': 200,
            'label': 'IDE 0',
            'summary': 'IDE 0',
            'type': 'VirtualIDEController',
            'unitNumber': None
        },
        201: {
            '_obj': '...',
            'busNumber': 1,
            'devices': [],
            'key': 201,
            'label': 'IDE 1',
            'summary': 'IDE 1',
            'type': 'VirtualIDEController',
            'unitNumber': None
        },
        300: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [600, 700],
            'key': 300,
            'label': 'PS2 controller 0',
            'summary': 'PS2 controller 0',
            'type': 'VirtualPS2Controller',
            'unitNumber': None
        },
        400: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [],
            'key': 400,
            'label': 'SIO controller 0',
            'summary': 'SIO controller 0',
            'type': 'VirtualSIOController',
            'unitNumber': None
        },
        500: {
            '_obj': '...',
            'key': 500,
            'label': 'Video card',
            'summary': 'Video card',
            'type': 'VirtualMachineVideoCard',
            'unitNumber': 0,
            'videoRamSizeInKB': 8192
        },
        600: {
            '_obj': '...',
            'key': 600,
            'label': 'Keyboard',
            'summary': 'Keyboard',
            'type': 'VirtualKeyboard',
            'unitNumber': 0
        },
        700: {
            '_obj': '...',
            'key': 700,
            'label': 'Pointing device',
            'summary': 'Pointing device; Device',
            'type': 'VirtualPointingDevice',
            'unitNumber': 1
        },
        1000: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [2000],
            'key': 1000,
            'label': 'SCSI controller 0',
            'summary': 'LSI Logic SAS',
            'type': 'VirtualLsiLogicSASController',
            'unitNumber': 3
        },
        2000: {
            '_obj': '...',
            'capacityInKB': 283115520,
            'key': 2000,
            'label': 'Hard disk 1',
            'summary': '283,115,520 KB',
            'type': 'VirtualDisk',
            'unitNumber': 0
        },
        3000: {
            '_obj': '...',
            'key': 3000,
            'label': 'CD/DVD drive 1',
            'summary': 'Remote device',
            'type': 'VirtualCdrom',
            'unitNumber': 0
        },
        4000: {
            '_obj': '...',
            'addressType': 'generated',
            'key': 4000,
            'label': 'Network adapter 1',
            'macAddress': '...',
            'summary': 'internal',
            'type': 'VirtualVmxnet3',
            'unitNumber': 7,
        },
        7000: {
            '_obj': '...',
            'busNumber': 0,
            'devices': [],
            'key': 7000,
            'label': 'USB controller',
            'summary': 'Auto connect Disabled',
            'type': 'VirtualUSBController',
            'unitNumber': 22
        },
        12000: {
            '_obj': '...',
            'key': 12000,
            'label': 'VMCI device',
            'summary': 'Device on the virtual machine PCI bus that provides '
                       'support for the virtual machine communication '
                       'interface',
            'type': 'VirtualMachineVMCIDevice',
            'unitNumber': 17
        }
    },
    'disks': [
        {
            'capacity': 283115520,
            'committed': 283115520,
            'descriptor': '[datastore1] s123.vmdk',
            'device': {
                '_obj': '...',
                'capacityInKB': 283115520,
                'key': 2000,
                'label': 'Hard disk 1',
                'summary': '283,115,520 KB',
                'type': 'VirtualDisk',
                'unitNumber': 0
            },
            'files': [
                {
                    'key': 4,
                    'name': '[datastore1] s.vmdk',
                    'size': 0,
                    'type': 'diskDescriptor'
                },
                {
                    'key': 5,
                    'name': '[datastore1] s-flat.vmdk',
                    'size': 289910292480,
                    'type': 'diskExtent'
                }
            ],
            'label': 'Hard disk 1'
        }
    ],
    'files': {
        0: {
            'key': 0,
            'name': '[datastore1] s.vmx',
            'size': 2724,
            'type': 'config'
        },
        1: {
            'key': 1,
            'name': '[datastore1] s.vmxf',
            'size': 3237,
            'type': 'extendedConfig'
        },
        2: {
            'key': 2,
            'name': '[datastore1] s.nvram',
            'size': 74232,
            'type': 'nvram'
        },
        3: {
            'key': 3,
            'name': '[datastore1] s.vmsd',
            'size': 0,
            'type': 'snapshotList'
        },
        4: {
            'key': 4,
            'name': '[datastore1] s.vmdk',
            'size': 0,
            'type': 'diskDescriptor'
        },
        5: {
            'key': 5,
            'name': '[datastore1] s-flat.vmdk',
            'size': 289910292480,
            'type': 'diskExtent'
        },
        6: {
            'key': 6,
            'name': '[datastore1] s/vmware-1.log',
            'size': 238122,
            'type': 'log'
        },
        7: {
            'key': 7,
            'name': '[datastore1] sample/vmware.log',
            'size': 2585558621,
            'type': 'log'
        },
        8: {
            'key': 8,
            'name': '[datastore1] s1.vswp',
            'size': 204010946560,
            'type': 'swap'
        },
        9: {
            'key': 9,
            'name': '[datastore1] s1.vswp',
            'size': 139460608,
            'type': 'uwswap'
        }
    },
    'guest_full_name': 'Microsoft Windows Server 2008 R2 (64-bit)',
    'guest_id': 'windows7Server64Guest',
    'hostname': 'app-1.internal',
    'ip_address': '10.10.10.11',
    'memory_mb': 194560,
    'name': 'APP-123',
    'net': [
        {
            'connected': True,
            'ip_addresses': ['10.10.10.11'],
            'mac_address': '00:22:33:cc:bb:aa',
            'network': 'internal'
        }
    ],
    'num_cpu': 8,
    'path': '[datastore1] sample/sample.vmx'
}

VMWARE_SAMPLE_SUBDEV_NO_MAC = {
    'devices': {
        100: {
           '_obj': '...',
            'busNumber': 0,
            'devices': [500, 12000, 1000, 4000],
            'key': 100,
            'label': 'PCI controller 0',
            'summary': 'PCI controller 0',
            'type': 'VirtualPCIController',
            'unitNumber': None
        },
        200: {'_obj': '...',
              'busNumber': 0,
              'devices': [3000],
              'key': 200,
              'label': 'IDE 0',
              'summary': 'IDE 0',
              'type': 'VirtualIDEController',
              'unitNumber': None
        },
        201: {'_obj': '...',
              'busNumber': 1,
              'devices': [],
              'key': 201,
              'label': 'IDE 1',
              'summary': 'IDE 1',
              'type': 'VirtualIDEController',
              'unitNumber': None
        },
        300: {'_obj': '...',
              'busNumber': 0,
              'devices': [600, 700],
              'key': 300,
              'label': 'PS2 controller 0',
              'summary': 'PS2 controller 0',
              'type': 'VirtualPS2Controller',
              'unitNumber': None
        },
        400: {'_obj': '...',
              'busNumber': 0,
              'devices': [],
              'key': 400,
              'label': 'SIO controller 0',
              'summary': 'SIO controller 0',
              'type': 'VirtualSIOController',
              'unitNumber': None
        },
        500: {'_obj': '...',
              'key': 500,
              'label': 'Video card',
              'summary': 'Video card',
              'type': 'VirtualMachineVideoCard',
              'unitNumber': 0,
              'videoRamSizeInKB': 4096
        },
        600: {'_obj': '...',
              'key': 600,
              'label': 'Keyboard',
              'summary': 'Keyboard',
              'type': 'VirtualKeyboard',
              'unitNumber': 0
        },
        700: {'_obj': '...',
              'key': 700,
              'label': 'Pointing device',
              'summary': 'Pointing device; Device',
              'type': 'VirtualPointingDevice',
              'unitNumber': 1
        },
        1000: {'_obj': '...',
               'busNumber': 0,
               'devices': [2000],
               'key': 1000,
               'label': 'SCSI controller 0',
               'summary': 'LSI Logic',
               'type': 'VirtualLsiLogicController',
               'unitNumber': 3
        },
        2000: {'_obj': '...',
               'capacityInKB': 52428800,
               'key': 2000,
               'label': 'Hard disk 1',
               'summary': '52,428,800 KB',
               'type': 'VirtualDisk',
               'unitNumber': 0
        },
        3000: {'_obj': '...',
               'key': 3000,
               'label': 'CD/DVD drive 1',
               'summary': 'ISO [] /usr/lib/vmware/isoimages/linux.iso',
               'type': 'VirtualCdrom',
               'unitNumber': 0
        },
        4000: {'_obj': '...',
               'addressType': 'generated',
               'key': 4000,
               'label': 'Network adapter 1',
               'macAddress': 'aa:bb:cc:dd:ee:ff',
               'summary': 'vlan960',
               'type': 'VirtualE1000',
               'unitNumber': 7
        },
        12000: {'_obj': '...',
                'key': 12000,
                'label': 'VMCI device',
                'summary': 'Device on the virtual machine PCI bus that provides support for the virtual machine communication interface',
                'type': 'VirtualMachineVMCIDevice',
                'unitNumber': 17
        }
    },
    'disks': [{
        'capacity': 52428800,
        'committed': 6762496,
        'descriptor': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmdk',
        'device': {'_obj': '...',
                   'capacityInKB': 52428800,
                   'key': 2000,
                   'label': 'Hard disk 1',
                   'summary': '52,428,800 KB',
                   'type': 'VirtualDisk',
                   'unitNumber': 0},
        'files': [{'key': 3,
                   'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmdk',
                   'size': 0,
                   'type': 'diskDescriptor'},
                  {'key': 4,
                   'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a-flat.vmdk',
                   'size': 6924795904,
                   'type': 'diskExtent'}],
        'label': 'Hard disk 1'
    }],
    'files': {
        0: {'key': 0,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmx',
            'size': 2096,
            'type': 'config'},
        1: {'key': 1,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmxf',
            'size': 0,
            'type': 'extendedConfig'},
        2: {'key': 2,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmsd',
            'size': 0,
            'type': 'snapshotList'},
        3: {'key': 3,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmdk',
            'size': 0,
            'type': 'diskDescriptor'},
        4: {'key': 4,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a-flat.vmdk',
            'size': 6924795904,
            'type': 'diskExtent'},
        5: {'key': 5,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.nvram',
            'size': 8684,
            'type': 'nvram'},
        6: {'key': 6,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a-929d0ddb.vswp',
            'size': 2147483648,
            'type': 'swap'},
        7: {'key': 7,
            'name': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/vmx-SevOne-vPAS-free-v5.3.2.0a-2459766235-1.vswp',
            'size': 115343360,
            'type': 'uwswap'}
    },
    'guest_full_name': 'Other 2.6.x Linux (64-bit)',
    'guest_id': 'other26xLinux64Guest',
    'memory_mb': 2048,
    'name': 'sample_name',
    'num_cpu': 2,
    'path': '[datastore1] SevOne-vPAS-free-v5.3.2.0a/SevOne-vPAS-free-v5.3.2.0a.vmx'
}
