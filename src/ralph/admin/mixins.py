# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import reversion

from django.db import models

from ralph.admin import widgets


FORMFIELD_FOR_DBFIELD_DEFAULTS = {
    models.DateField: {'widget': widgets.AdminDateWidget},
}


class RalphAdminMixin(object):

    """Ralph admin mixin."""

    extra_views = []
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
    def __init__(self, *args, **kwargs):
        super(RalphAdminMixin, self).__init__(*args, **kwargs)
        self.formfield_overrides.update(FORMFIELD_FOR_DBFIELD_DEFAULTS)
