#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.cmdb.views import BaseCMDBView

class Graphs(BaseCMDBView):
    template_name = 'cmdb/graphs.html'

    def get_context_data(self, **kwargs):
        ret = super(BaseCMDBView, self).get_context_data(**kwargs)
        ret.update({
        })
        return ret

