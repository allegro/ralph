# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ralph.admin import ralph_site


class RalphExtraViewMixin(object):
    # TODO: permissions, breadcrumbs
    # TODO: highlighting active tab
    name = None
    extra_view_base_template = None

    def get_name(self):
        if not self.name:
            raise NotImplementedError(
                'Please define name for {}'.format(self.__class__)
            )
        return self.name

    def get_extra_view_base_template(self):
        if not self.extra_view_base_template:
            raise NotImplementedError(
                'Please define base template for {}'.format(self.__class__)
            )
        return self.extra_view_base_template

    def get_context_data(self, **kwargs):
        context = super(RalphExtraViewMixin, self).get_context_data(**kwargs)
        context.update(ralph_site.each_context(self.request))
        context['BASE_TEMPLATE'] = self.get_extra_view_base_template()
        context['label'] = self.label
        return context

    def get_template_names(self):
        templates = []
        app_label = self.model._meta.app_label
        model = self.model._meta.model_name
        if self.template_name:
            templates = [self.template_name]
        templates.extend([
            '{}/{}.html'.format(model, self.get_name()),
            '{}/{}/{}.html'.format(app_label, model, self.get_name())
        ])
        return templates


class RalphListView(RalphExtraViewMixin, TemplateView):
    extra_view_base_template = 'ralph_admin/extra_views/base_list.html'

    def dispatch(self, request, model, *args, **kwargs):
        self.model = model
        return super(RalphListView, self).dispatch(request, *args, **kwargs)


class RalphDetailView(RalphExtraViewMixin, TemplateView):
    extra_view_base_template = 'ralph_admin/extra_views/base_change.html'

    def dispatch(self, request, model, pk, *args, **kwargs):
        self.model = model
        self.object = get_object_or_404(model.objects, pk=pk)
        return super(RalphDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(RalphDetailView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context
