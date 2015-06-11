# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import url
from django.contrib.admin.sites import AdminSite


def get_urls_chunks(model, view):
    """
    Returns a tuple to generate a URL for an additional view

    :Example:

        >>> "{}_{}_{}".format(*get_urls_chunks(model, view))
        app_label_model_name_url_name

    :param model: Django admin model
    :type model: models.Model
    :param view: Django generic view object
    :type view: GenericView

    :return: tuple of names
    :rtype: tuple
    """

    return (
        model._meta.app_label, model._meta.model_name, view.url_name
    )


class RalphAdminSiteMixin(object):

    """Ralph admin site mixin."""

    site_header = settings.ADMIN_SITE_HEADER
    index_template = 'admin/index.html'
    app_index_template = 'ralph_admin/app_index.html'
    object_history_template = 'ralph_admin/object_history.html'

    def get_urls(self, *args, **kwargs):
        """Override django admin site get_urls method."""
        urlpatterns = super(RalphAdminSiteMixin, self).get_urls(
            *args, **kwargs
        )
        for model, model_admin in self._registry.items():
            for view in model_admin.extra_views:
                # insert at the begin
                urlpatterns.insert(0, url(
                    '^{}/{}/{}/$'.format(*get_urls_chunks(model, view)),
                    view.as_view(),
                    name='{}_{}_{}'.format(*get_urls_chunks(model, view))
                ))
        return urlpatterns


class RalphAdminSite(RalphAdminSiteMixin, AdminSite):
    pass


ralph_site = RalphAdminSite(name='ralph_site')
