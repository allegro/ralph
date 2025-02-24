# -*- coding: utf-8 -*-
from django.conf import settings

DEFAULT_ASYNC_TRANSITION_SERVICE_NAME = 'ASYNC_TRANSITIONS'
TRANSITION_ATTR_TAG = 'transition_action'
TRANSITION_ORIGINAL_STATUS = (0, 'Keep orginal status')

REPORTS_MAPPER = settings.RELEASE_REPORT_CONFIG['REPORTS_MAPPER']
DEFAULT_REPORT = settings.RELEASE_REPORT_CONFIG['DEFAULT_REPORT']


def get_report_name_for_transition_id(transition_id):
    return REPORTS_MAPPER.get(str(transition_id), DEFAULT_REPORT)
