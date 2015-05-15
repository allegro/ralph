# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.admin.sites import AdminSite


class RalphAdminMixin(object):
    site_header = 'Ralph 3'

    def each_context(self, request):
        context = super(RalphAdminMixin, self).each_context(request)
        context['registry'] = self._registry
        return context

    def get_urls(self, *args, **kwargs):
        def get_chunks(model, view):
            return (
                model._meta.app_label, model._meta.model_name, view.url_name
            )
        urlpatterns = super(RalphAdminMixin, self).get_urls(*args, **kwargs)
        for model, model_admin in self._registry.items():
            for view in model_admin.extra_views:
                # insert at the begin
                urlpatterns.insert(0, url(
                    '^{}/{}/{}/'.format(*get_chunks(model, view)),
                    view.as_view(),
                    name='{}_{}_{}'.format(*get_chunks(model, view))
                ))
        return urlpatterns


class RalphAdminSite(RalphAdminMixin, AdminSite):
    pass


ralph_site = RalphAdminSite(name='myadmin')
