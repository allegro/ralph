# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.views.main import SEARCH_VAR
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic import View

from ralph.admin.decorators import register_extra_view
from ralph.admin.mixins import RalphAdmin
from ralph.admin.sites import ralph_site
from ralph.admin.views.extra import RalphDetailView, RalphListView
from ralph.admin.views.main import RalphChangeList
from ralph.tests.admin import CarAdmin, ManufacturerAdmin
from ralph.tests.factories import UserFactory
from ralph.tests.mixins import ClientMixin, ReloadUrlsMixin
from ralph.tests.models import Car, Foo, TestManufacturer


class ExtraListView(RalphListView, View):
    label = "Extra list view"
    name = "list"
    url_name = "extra_list_view"


class ExtraDetailView(RalphDetailView, View):
    label = "Extra detail view"
    name = "detail"
    url_name = "extra_detail_view"


def new_test_view(klass, view_name=None):
    view_name = view_name or "test_view_{}".format(new_test_view.counter)

    class TestView(klass):
        label = "Test view {}".format(new_test_view.counter)
        name = url_name = view_name
        template_name = "tests/foo/detail.html"

    new_test_view.counter += 1
    return TestView


new_test_view.counter = 0


class ExtraViewsTest(ReloadUrlsMixin, ClientMixin, TestCase):
    def setUp(self):  # noqa
        super(ExtraViewsTest, self).setUp()
        if ralph_site.is_registered(Foo):
            ralph_site.unregister(Foo)
        self.reload_urls()
        self.login_as_user()

    def _register_model_in_admin(self, model, admin_model=RalphAdmin):
        ralph_site.register([model], admin_class=admin_model)
        self.reload_urls()

    def test_dynamic_register_model_to_admin_panel(self):
        """
        Dynamic register model to admin panel.
        """
        self._register_model_in_admin(Foo)
        response = self.client.get(reverse("admin:tests_foo_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_extra_list_view_via_class_attr(self):
        """
        Added extra view to list view by added to admin class.
        """

        class FooListAdmin(RalphAdmin):
            list_views = [type("ExtraListView", (ExtraListView,), {})]

        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(reverse("admin:tests_foo_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["list_views"][0].label, ExtraListView.label)

    def test_extra_change_view_via_class_attr(self):
        """
        Added extra view to change view by added to admin class.
        """
        obj = Foo.objects.create(bar="test")

        class FooChangeAdmin(RalphAdmin):
            change_views = [type("ExtraDetailView", (ExtraDetailView,), {})]

        self._register_model_in_admin(Foo, FooChangeAdmin)

        response = self.client.get(
            reverse("admin:tests_foo_change", args=(obj.pk,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["change_views"][0].label, ExtraDetailView.label
        )

    def test_visit_extra_list_view(self):
        """
        Visit extra list view.
        """

        class FooListAdmin(RalphAdmin):
            list_views = [type("ExtraListView", (ExtraListView,), {})]

        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(
            reverse("admin:tests_foo_extra_list_view"), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_visit_extra_detail_view(self):
        """
        Added extra view to list view by added to admin class.
        """
        obj = Foo.objects.create(bar="test")

        class FooListAdmin(RalphAdmin):
            change_views = [type("ExtraDetailView", (ExtraDetailView,), {})]

        self._register_model_in_admin(Foo, FooListAdmin)

        response = self.client.get(
            reverse("admin:tests_foo_extra_detail_view", args=(obj.pk,)), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_extra_list_view_via_decorator(self):
        """
        Register extra view by decorator.
        """
        self._register_model_in_admin(Foo)

        @register_extra_view(Foo)
        class TestView(new_test_view(RalphListView)):
            pass

        self.reload_urls()
        response = self.client.get(reverse("admin:tests_foo_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["list_views"][0].label, TestView.label)

    def test_extra_change_view_via_decorator(self):
        """
        Register extra view by decorator.
        """
        obj = Foo.objects.create(bar="test")
        self._register_model_in_admin(Foo)

        @register_extra_view(Foo)
        class TestView(RalphDetailView, View):
            label = "Test view"
            url_name = "extra_detail_view"

        self.reload_urls()
        response = self.client.get(
            reverse("admin:tests_foo_change", args=(obj.pk,)), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["change_views"][0].label, TestView.label)

    def test_register_decorator_raise_value_error_incorrect_view_type(self):
        """
        Register decorator raise ValueError when model is incorrect.
        """
        self._register_model_in_admin(Foo)
        with self.assertRaises(ValueError):

            @register_extra_view(Foo)
            class TestView(RalphListView):
                _type = "incorrect_type"

    def test_register_decorator_raise_value_error_incorrect_target_view(self):
        """
        Register decorator raise ValueError when target view is incorrect.
        """
        self._register_model_in_admin(Foo)
        with self.assertRaises(ValueError):

            @register_extra_view(Foo)
            class TestView(View):
                pass

    def test_many_tabs_link(self):
        """
        Test links in tabs.
        """
        obj = Foo.objects.create(bar="test")
        endpoints = [(RalphDetailView, "test_url_1"), (RalphDetailView, "test_url_2")]
        views = [new_test_view(klass, name) for klass, name in endpoints]

        class FooAdmin(RalphAdmin):
            change_views = views

        self._register_model_in_admin(Foo, FooAdmin)

        response = self.client.get(
            reverse("admin:tests_foo_change", args=(obj.pk,)), follow=True
        )
        tabs = response.context["change_views"]
        for tab in tabs:
            resp = self.client.get(
                reverse(
                    tab.url_with_namespace,
                    args=[
                        obj.pk,
                    ],
                )
            )
            self.assertEqual(resp.status_code, 200)


@ddt
class ChangeListTest(TestCase):
    def setUp(self):
        super().setUp()
        manufacturer = TestManufacturer.objects.create(name="test", country="pl")
        TestManufacturer.objects.create(name="test2", country="pl2")
        Car.objects.create(year=2015, name="test", manufacturer=manufacturer)
        Car.objects.create(
            year=2014, name="AutotompleteTest 2", manufacturer=manufacturer
        )
        Car.objects.create(
            year=2015, name="AutotompleteTest", manufacturer=manufacturer
        )

    def _change_list_factory(self, model, model_admin, request, list_display=None):
        return RalphChangeList(
            date_hierarchy=model_admin.date_hierarchy,
            list_display=list_display or model_admin.list_display,
            list_display_links=model_admin.list_display_links,
            list_editable=model_admin.list_editable,
            list_filter=model_admin.list_filter,
            list_max_show_all=model_admin.list_max_show_all,
            list_per_page=model_admin.list_per_page,
            list_select_related=model_admin.list_select_related,
            search_fields=model_admin.search_fields,
            model=model,
            model_admin=model_admin(model, ralph_site),
            request=request,
            sortable_by=model_admin.sortable_by,
        )

    def _get_ordering_list(self, model, model_admin, params, list_display):
        from django.contrib.admin.views.main import ORDER_VAR

        get_params = "{}={}".format(ORDER_VAR, ".".join(map(str, params)))
        request = RequestFactory().get("/?" + get_params)
        request.user = UserFactory()
        cl = self._change_list_factory(
            model=Car, model_admin=CarAdmin, request=request, list_display=list_display
        )
        return cl.get_ordering(request, model.objects.all())

    @unpack
    @data(
        (
            [1],
            ["pk", "name", "manufacturer"],
            ["name", "-pk"],
        ),
        (
            [1, 2],
            ["pk", "name", "manufacturer"],
            ["name", "manufacturer__name", "manufacturer__country", "-pk"],
        ),
        (
            [-1, -2],
            ["pk", "name", "manufacturer"],
            ["-name", "-manufacturer__name", "-manufacturer__country", "-pk"],
        ),
        (
            [-1, 2, 3],
            ["pk", "name", "year", "manufacturer"],
            ["-name", "year", "manufacturer__name", "manufacturer__country", "-pk"],
        ),
        (
            [-1, 3, 2],
            ["pk", "name", "year", "manufacturer"],
            ["-name", "manufacturer__name", "manufacturer__country", "year", "-pk"],
        ),
        (
            [3, 2, 1],
            ["pk", "name", "year", "manufacturer"],
            ["manufacturer__name", "manufacturer__country", "year", "name", "-pk"],
        ),
        (
            [2, 1, 0],
            ["name", "year", "manufacturer"],
            ["manufacturer__name", "manufacturer__country", "year", "name", "-pk"],
        ),
        (
            [1, 2, 0],
            ["name", "year", "manufacturer"],
            ["year", "manufacturer__name", "manufacturer__country", "name", "-pk"],
        ),
    )
    def test_sort_related(self, ordering_params, list_display, expected_ordering):
        ordering = self._get_ordering_list(
            Car,
            CarAdmin,
            ordering_params,
            list_display,
        )
        self.assertEqual(expected_ordering, ordering)

    def test_get_queryset_autocomplete(self):
        request = RequestFactory().get("/car", data={IS_POPUP_VAR: 1})
        change_list = self._change_list_factory(
            model=Car, model_admin=CarAdmin, request=request, list_display=["id"]
        )
        resutlt = change_list.get_queryset(request)
        self.assertEqual(len(resutlt), 2)

    def test_get_queryset_aucotomplete_search(self):
        request = RequestFactory().get(
            "/car", data={IS_POPUP_VAR: 1, SEARCH_VAR: "autotompletetest"}
        )
        change_list = self._change_list_factory(
            model=Car, model_admin=CarAdmin, request=request, list_display=["id"]
        )
        resutlt = change_list.get_queryset(request)
        self.assertEqual(len(resutlt), 1)

    def test_get_queryset(self):
        request = RequestFactory().get("/manufacturer", data={IS_POPUP_VAR: 1})
        change_list = self._change_list_factory(
            model=TestManufacturer,
            model_admin=ManufacturerAdmin,
            request=request,
            list_display=["id"],
        )
        resutlt = change_list.get_queryset(request)
        self.assertEqual(len(resutlt), 2)
