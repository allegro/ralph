# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.util.demo import DemoData, register

from ralph_assets.tests.utils.assets import (
    DataCenterFactory,
    RackFactory,
    ServerRoomFactory,
)


@register
class DemoDataCenter(DemoData):
    name = 'dc'
    title = 'DC'
    required = ['deprecated_dc']

    def generate_data(self, data):
        return {
            'a': DataCenterFactory.create(
                name='DC A',
                deprecated_ralph_dc=data['deprecated_dc']['a'],
            ),
            'b': DataCenterFactory.create(
                name='DC B',
                deprecated_ralph_dc=data['deprecated_dc']['b'],
            ),
        }


@register
class DemoServerRoom(DemoData):
    name = 'server_rooms'
    title = 'Server rooms'
    required = ['dc']

    def generate_data(self, data):
        dc = data['dc']['a']
        return {
            'a': ServerRoomFactory(
                name='Server Room A',
                data_center=dc,
            ),
            'b': ServerRoomFactory(
                name='Server Room B',
                data_center=dc,
            ),
        }


@register
class DemoRack(DemoData):
    name = 'racks'
    title = 'Racks'
    required = ['deprecated_racks', 'dc', 'server_rooms']

    def generate_data(self, data):
        return {
            'a': RackFactory(
                name=data['deprecated_racks']['a'].name,
                data_center=data['dc']['a'],
                server_room=data['server_rooms']['a'],
                deprecated_ralph_rack=data['deprecated_racks']['a'],
                visualization_row=1,
                visualization_col=1,
            ),
            'b': RackFactory(
                name=data['deprecated_racks']['b'].name,
                data_center=data['dc']['b'],
                server_room=data['server_rooms']['b'],
                deprecated_ralph_rack=data['deprecated_racks']['b'],
                visualization_row=1,
                visualization_col=2,
            ),
        }
