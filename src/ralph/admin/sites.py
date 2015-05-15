# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict
import six

from django.apps import apps
from django.conf.urls import url
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import NoReverseMatch, reverse
from django.template.response import TemplateResponse
from django.utils.text import capfirst


class RalphAdminMixin(object):
    site_header = 'Ralph 3'
    index_template = 'admin/index.html'

    def index(self, request, extra_context=None):
        context = dict(
            self.each_context(request),
            title=self.index_title,
        )
        return TemplateResponse(
            request, self.index_template, context
        )

    def each_context(self, request):
        context = super(RalphAdminMixin, self).each_context(request)
        app_dict = {}
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
            has_module_perms = model_admin.has_module_permission(request)

            if has_module_perms:
                perms = model_admin.get_model_perms(request)
                if True in perms.values():
                    info = (app_label, model._meta.model_name)
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'object_name': model._meta.object_name,
                        'perms': perms,
                    }
                    model_dict['extra_views'] = []
                    for view in model_admin.extra_views:
                        model_dict['extra_views'].append(
                            {
                                'label': view.label,
                                'url': view.url_name,  # TODO
                            }
                        )
                    if perms.get('change', False):
                        try:
                            model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if perms.get('add', False):
                        try:
                            model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': apps.get_app_config(app_label).verbose_name,
                            'app_label': app_label,
                            'app_url': reverse(
                                'admin:app_list',
                                kwargs={'app_label': app_label},
                                current_app=self.name,
                            ),
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        # Sort the apps alphabetically.
        app_list = list(six.itervalues(app_dict))
        app_list.sort(key=lambda x: x['name'].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])
        context['app_list'] = app_list
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
