# -*- coding: utf-8 -*-
OPENSTACK_DATA = {
    'project_os_id1': {
        'name': 'project_os_1',
        'tag': 'tag1',
        'servers': {
            'host_os_1': {
                'hostname': 'host_os_1',
                'hypervisor': 'hypervisor1.dcn.net',
                'flavor_id': 'flavor_os_id1',
                'tag': 'tag1',
                'ips': ['10.1.0.1', '10.2.0.1'],
                'created': '2015-09-10T06:48:00Z',
            }
        }
    },
    'project_os_id2': {
        'name': 'project_os_2',
        'tag': 'tag2',
        'servers': {
            'host_os_2': {
                'hostname': 'host_os_2',
                'hypervisor': 'hypervisor1.dcn.net',
                'flavor_id': 'flavor_os_id2',
                'tag': 'tag2',
                'ips': ['10.3.0.1', '10.4.0.1'],
                'created': '2015-09-11T06:48:00Z',
            },
            'host_os_3': {
                'hostname': 'host_os_3',
                'hypervisor': 'hypervisor1.dcn.net',
                'flavor_id': 'flavor_os_id1',
                'tag': 'tag2',
                'ips': ['10.10.10.10'],
                'created': '2015-09-12T06:48:00Z',
                'modified': '2015-10-12T06:48:03Z'
            }
        }
    },
    'project_os_id3': {'name': 'project_os_3', 'tag': 'tag1', 'servers': {}},
    'project_id1': {'name': 'modified1', 'tag': 'tag1', 'servers': {
            'host_id_1': {
                'hostname': 'host_id_1',
                'hypervisor': 'hypervisor1.dcn.net',
                'flavor_id': 'flavor_os_id1',
                'tag': 'tag1',
                'ips': ['11.11.11.11'],
                'created': '2015-09-13T06:48:00Z',
                'modified': '2015-10-13T06:48:03Z'
            }
        }
    }
}

OPENSTACK_FLAVOR = {
    'flavor_os_id1': {
        'name': 'm1-c2-d6',
        'cores': 2,
        'memory': 1024,
        'disk': 6144,
        'tag': 'ab'
    },
    'flavor_os_id2': {
        'name': 'm2-c8-d20',
        'cores': 8,
        'memory': 2048,
        'disk': 20480,
        'tag': 'cd'
    },
    'flavor_id1': {
        'name': 'change_1',
        'cores': 4,
        'memory': 4096,
        'disk': 12288,
        'tag': 'ef'
    }
}

TEST_HOSTS = {
    'host_os_id1': {
        'hostname': 'host_test_1',
        'hypervisor': 'hypervisor_os1.dcn.net',
        'flavor_id': 'flavor_id1',
        'tag': 'tag2',
        'ips': ['10.10.10.10'],
        'created': '2015-09-14T06:48:00Z',
        'modified': '2015-10-14T06:48:03Z'
    },
    'host_os_id2': {
        'hostname': 'host_test_2',
        'hypervisor': 'hypervisor_os1.dcn.net',
        'flavor_id': 'flavor_id1',
        'tag': 'tag3',
        'ips': ['10.10.10.11'],
        'created': '2015-09-15T06:48:00Z',
        'modified': '2015-10-15T06:48:03Z'
    },
    'host_id1': {
        'hostname': 'host_mod_1',
        'hypervisor': 'hypervisor_os1.dcn.net',
        'flavor_id': 'flavor_id1',
        'tag': 'tag3',
        'ips': ['10.10.10.12'],
        'created': '2015-09-16T06:48:00Z',
        'modified': '2015-10-16T06:48:03Z'
    },
}
