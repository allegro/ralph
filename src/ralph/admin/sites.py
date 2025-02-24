# -*- coding: utf-8 -*-
from collections import defaultdict

from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.sites import AdminSite


class RalphAdminSiteMixin(object):
    """Ralph admin site mixin."""

    site_header = settings.ADMIN_SITE_HEADER
    site_title = settings.ADMIN_SITE_TITLE
    index_template = "admin/index.html"
    app_index_template = "admin/app_index.html"
    object_history_template = "admin/object_history.html"

    def _get_views(self, admin):
        return (admin.change_views or []) + (admin.list_views or [])

    def register(self, model_or_iterable, *args, **kwargs):
        super().register(model_or_iterable, *args, **kwargs)
        # operate on admin class instance to get processed extra views
        for model in model_or_iterable:
            if model._meta.swapped:
                continue
            admin_instance = self._registry[model]
            for view in self._get_views(admin_instance):
                view.post_register(self.name, model)

    def get_urls(self, *args, **kwargs):
        """Override django admin site get_urls method."""
        urlpatterns = super(RalphAdminSiteMixin, self).get_urls(*args, **kwargs)
        for model, model_admin in self._registry.items():
            for view in self._get_views(model_admin):
                urlpatterns.insert(
                    0,
                    url(
                        view.get_url_pattern(model),
                        view.as_view(),
                        {
                            "model": model,
                            "views": getattr(
                                model_admin, "{}_views".format(view._type), []
                            ),
                        },
                        name=view.url_to_reverse,
                    ),
                )
        return urlpatterns

    def get_extra_view_menu_items(self):
        """Method returns list of items for sitetree mechanism."""
        items = defaultdict(list)

        def get_item(model, view, change_view=False):
            url = view.url_with_namespace
            if change_view:
                url += " object.id"
            return {"title": view.label, "url": url}

        for model, model_admin in self._registry.items():
            name = "{}_{}".format(model._meta.app_label, model._meta.model_name)
            for view in model_admin.list_views or []:
                items[name].append(get_item(model, view))
            for view in model_admin.change_views or []:
                items[name].append(get_item(model, view, True))
        return items

    def index(self, request, extra_context=None):
        from ralph.data_center.models import DataCenter

        if extra_context is None:
            extra_context = {}
        extra_context["data_centers"] = DataCenter.objects.filter(
            show_on_dashboard=True
        )
        return super().index(request, extra_context)

    def get_admin_instance_for_model(self, model_class):
        return ralph_site._registry.get(model_class, None)


class RalphAdminSite(RalphAdminSiteMixin, AdminSite):
    def each_context(self, request):
        context = super(RalphAdminSite, self).each_context(request)
        context["google_tag_manager_tag_id"] = settings.GOOGLE_TAG_MANAGER_TAG_ID
        return context


ralph_site = RalphAdminSite()
