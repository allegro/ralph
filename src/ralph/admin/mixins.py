# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import reversion


class RalphAdminMixin(object):

    """Ralph admin mixin."""

    change_list_template = 'ralph_admin/change_list.html'
    change_form_template = 'ralph_admin/change_form.html'

    def changelist_view(self, request, extra_context=None):
        """Override change list from django."""
        if extra_context is None:
            extra_context = {}
        extra_context['app_label'] = self.model._meta.app_label
        extra_views = []
        for view in self.extra_views:
            extra_views.append({
                'label': view.label,
                'url': '{}/'.format(view.url_name),
            })
        extra_context['extra_views'] = extra_views
        return super(RalphAdminMixin, self).changelist_view(
            request, extra_context
        )


class RalphAdmin(RalphAdminMixin, reversion.VersionAdmin):
    extra_views = []
