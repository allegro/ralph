# -*- coding: utf-8 -*-
from copy import copy

from django.shortcuts import get_object_or_404

from ralph.admin.mixins import (
    get_common_media,
    get_inline_media,
    RalphAdmin,
    RalphTemplateView
)
from ralph.admin.sites import ralph_site
from ralph.lib.permissions.views import PermissionViewMetaClass

VIEW_TYPES = CHANGE, LIST = ('change', 'list')


class RalphExtraViewMixin(object):
    # TODO: permissions
    extra_view_base_template = None
    icon = None
    name = None
    template_name = None

    def dispatch(self, request, model, views, *args, **kwargs):
        self.model = model
        self.views = views
        return super(RalphExtraViewMixin, self).dispatch(
            request, *args, **kwargs
        )

    @classmethod
    def post_register(cls, namespace, model):
        cls.namespace = namespace
        cls.url_to_reverse = '{}_{}_{}'.format(
            model._meta.app_label, model._meta.model_name, cls.url_name
        )
        cls.url_with_namespace = ':'.join([
            cls.namespace, cls.url_to_reverse
        ])

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
        context['view_name'] = self.name
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


class RalphListView(RalphExtraViewMixin, RalphTemplateView):
    _type = LIST
    extra_view_base_template = 'admin/extra_views/base_list.html'

    def get_context_data(self, **kwargs):
        context = super(RalphListView, self).get_context_data(**kwargs)
        context['change_views'] = self.views
        return context

    @classmethod
    def get_url_pattern(cls, model):
        return r'^{}/{}/{}/$'.format(
            model._meta.app_label, model._meta.model_name, cls.url_name
        )


class AdminViewBase(type):
    def __new__(cls, name, bases, attrs):
        base_template = 'admin/extra_views/base_admin_change.html'
        empty_fieldset = (('__empty__', {'fields': []}),)
        admin_whitelist = ['inlines', 'fieldsets']
        admin_attrs = {
            key: attrs.pop(key, []) for key in admin_whitelist
        }
        admin_attrs['change_form_template'] = base_template
        admin_attrs['fieldsets'] = admin_attrs['fieldsets'] or empty_fieldset
        new_class = super().__new__(cls, name, bases, attrs)
        new_class.admin_class = type('AdminView', (RalphAdmin,), admin_attrs)
        return new_class


PermissionAdminViewBase = type(
    'PermissionAdminViewBase',
    (PermissionViewMetaClass, AdminViewBase),
    {}
)


class RalphDetailView(
    RalphExtraViewMixin, RalphTemplateView, metaclass=PermissionAdminViewBase
):
    _type = CHANGE
    extra_view_base_template = 'admin/extra_views/base_change.html'

    def dispatch(self, request, model, pk, *args, **kwargs):
        self.object = get_object_or_404(model, pk=pk)
        return super(RalphDetailView, self).dispatch(
            request, model, *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        context = super(RalphDetailView, self).get_context_data(**kwargs)
        context['object'] = self.object
        context['original'] = self.object
        context['change_views'] = self.views
        context['media'] += get_common_media() + get_inline_media()
        return context

    @classmethod
    def get_url_pattern(cls, model):
        return r'^{}/{}/(?P<pk>[0-9]+)/{}/$'.format(
            model._meta.app_label, model._meta.model_name, cls.url_name
        )


class RalphDetailViewAdmin(RalphDetailView):
    """This class helps to display standard model admin in tab."""
    def dispatch(self, request, model, pk, *args, **kwargs):
        self.object = get_object_or_404(model, pk=pk)
        self.views = kwargs['views']
        extra_context = copy(super().get_context_data())
        extra_context['object'] = self.object
        self.admin_class_instance = self.admin_class(
            model, ralph_site, change_views=self.views
        )
        extra_context['media'] += self.admin_class_instance.media
        return self.admin_class_instance.change_view(
            request,
            pk,
            extra_context=extra_context
        )
