# -*- coding: utf-8 -*-
"""The pluggable app definitions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.app import RalphModule


class Cmdb(RalphModule):
    """CMDB main application."""

    url_prefix = 'cmdb'
    module_name = 'ralph.cmdb'
    disp_name = 'CMDB'
    icon = 'fugue-thermometer'
    default_settings_module = 'ralph.settings'

    def __init__(self, **kwargs):
        super(Cmdb, self).__init__(
            'ralph.cmdb',
            distribution='ralph',
            **kwargs
        )
        self.append_app()
        self.insert_templates(__file__)
        self.register_logger('ralph.cmdb', {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        })
