#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.ui.views.common import Base


class ReportList(Base):
    section = 'reports'
    template_name = 'ui/report_list.html'
