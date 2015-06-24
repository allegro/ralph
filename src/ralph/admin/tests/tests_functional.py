# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.views.generic import View

from ralph.admin import RalphAdmin
from ralph.admin.decorators import register_extra_view, WrongViewClassError
from ralph.admin.sites import ralph_site
from ralph.admin.views import RalphDetailView, RalphListView
from ralph.tests.mixins import ClientMixin, ReloadUrlsMixin
from ralph.tests.models import Foo


class ExtraListView(RalphListView, View):
    label = 'Extra list view'
    name = 'list'
    url_name = 'extra_list_view'


class ExtraDetailView(RalphDetailView, View):
    label = 'Extra detail view'
    name = 'detail'
    url_name = 'extra_detail_view'


class ExtraViewsTest(ReloadUrlsMixin, ClientMixin, TestCase):

    def setUp(self):  # noqa
        super(ExtraViewsTest, self).setUp()
        if ralph_site.is_registered(Foo):
            ralph_site.unregister(Foo)
        self.reload_urls()
        self.login_as_user()

    def _register_model_in_admin(self, model, admin_model=RalphAdmin):
        ralph_site.register(model, admin_model)
        self.reload_urls()

    def test_dynamic_register_model_to_admin_panel(self):
        """
        Dynamic register model to admin panel.
        """
        self._register_model_in_admin(Foo)
        response = self.client.get(
            reverse('ralph_site:tests_foo_changelist'), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_extra_list_view_via_class_attr(self):
        """
        Added extra view to list view by added to admin class.
        """
        class FooListAdmin(RalphAdmin):
            list_views = [ExtraListView]
        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(
            reverse('ralph_site:tests_foo_changelist'), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['list_views'][0].label, ExtraListView.label
        )

    def test_extra_change_view_via_class_attr(self):
        """
        Added extra view to change view by added to admin class.
        """
        obj = Foo.objects.create(bar='test')

        class FooChangeAdmin(RalphAdmin):
            change_views = [ExtraDetailView]
        self._register_model_in_admin(Foo, FooChangeAdmin)

        response = self.client.get(
            reverse('ralph_site:tests_foo_change', args=(obj.pk,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['change_views'][0].label, ExtraDetailView.label
        )

    def test_visit_extra_list_view(self):
        """
        Visit extra list view.
        """
        class FooListAdmin(RalphAdmin):
            list_views = [ExtraListView]
        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(
            reverse('ralph_site:tests_foo_extra_list_view'), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_visit_extra_detail_view(self):
        """
        Added extra view to list view by added to admin class.
        """
        obj = Foo.objects.create(bar='test')

        class FooListAdmin(RalphAdmin):
            change_views = [ExtraDetailView]
        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(
            reverse('ralph_site:tests_foo_extra_detail_view', args=(obj.pk,)),
            follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_extra_list_view_via_decorator(self):
        """
        Register extra view by decorator.
        """
        @register_extra_view(Foo, register_extra_view.LIST)
        class TestView(RalphListView, View):
            label = 'Test view'
            url_name = 'extra_list_view'
        self._register_model_in_admin(Foo)

        response = self.client.get(
            reverse('ralph_site:tests_foo_changelist'), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['list_views'][0].label, TestView.label
        )

    def test_extra_change_view_via_decorator(self):
        """
        Register extra view by decorator.
        """
        obj = Foo.objects.create(bar='test')

        @register_extra_view(Foo, register_extra_view.CHANGE)
        class TestView(RalphDetailView, View):
            label = 'Test view'
            url_name = 'extra_detail_view'
        self._register_model_in_admin(Foo)

        response = self.client.get(
            reverse('ralph_site:tests_foo_change', args=(obj.pk,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['change_views'][0].label, TestView.label
        )

    def test_register_decorator_raise_value_error_model_and_view(self):
        """
        Register decorator raise ValueError with empty model and taget view.
        """
        with self.assertRaises(TypeError):
            @register_extra_view
            class TestView(View):
                pass

    def test_register_decorator_raise_value_error_incorrect_model(self):
        """
        Register decorator raise ValueError when model is incorrect.
        """
        with self.assertRaises(ValueError):
            @register_extra_view(ExtraDetailView, register_extra_view.LIST)
            class TestView(View):
                pass

    def test_register_decorator_raise_value_error_incorrect_target_view(self):
        """
        Register decorator raise ValueError when target view is incorrect.
        """
        with self.assertRaises(ValueError):
            @register_extra_view(Foo, 'incorrect value')
            class TestView(View):
                pass

    def test_register_to_wrong_view(self):
        """
        Register detail view to list and list view to change.
        """
        with self.assertRaises(WrongViewClassError):
            @register_extra_view(Foo, register_extra_view.LIST)
            class TestView(RalphDetailView):
                pass

        with self.assertRaises(WrongViewClassError):
            @register_extra_view(Foo, register_extra_view.CHANGE)
            class Test2View(RalphListView):
                pass
