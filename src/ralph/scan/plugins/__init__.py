# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import datetime


def get_base_result_template(plugin_name, messages=[]):
    return {
        'status': 'unknown',
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'plugin': plugin_name,
        'messages': messages,
    }
