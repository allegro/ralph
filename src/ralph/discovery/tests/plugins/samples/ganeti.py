#!/usr/bin/env python
# -*- coding: utf-8 -*-

raw_data = """
host1.dc1.local   gnt10.dc       gnt21.dc       -            99:ff:cc:90:22:33
host2.dc1         gnt11.dc       gnt20.dc       -            99:df:cc:90:22:09
host3.dc1         gnt10.dc       gnt20.dc       127.0.1.32   99:df:cc:90:33:09
host4.dc1         gnt111222.dc   gnt222111.dc   -            99:df:cc:90:33:aa
"""

parsed_data = [
    {
        'mac': '99FFCC902233',
        'ip': '',
        'host': 'host1.dc1.local',
        'secondary_nodes': 'gnt21.dc',
        'primary_node': 'gnt10.dc'
    },
    {
        'mac': '99DFCC902209',
        'ip': '',
        'host': 'host2.dc1',
        'secondary_nodes': 'gnt20.dc',
        'primary_node': 'gnt11.dc'
    },
    {
        'mac': '99DFCC903309',
        'ip': '127.0.1.32',
        'host': 'host3.dc1',
        'secondary_nodes': 'gnt20.dc',
        'primary_node': 'gnt10.dc'
    },
    {
        'mac': '99DFCC9033AA',
        'ip': '',
        'host': 'host4.dc1',
        'secondary_nodes': 'gnt222111.dc',
        'primary_node': 'gnt111222.dc'
    },
]
