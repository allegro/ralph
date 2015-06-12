# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import partial

from django.contrib.admin.decorators import register as django_register
from django.db.models import Model

from ralph.admin.signals import admin_get_list_views, admin_get_change_views
from ralph.admin.sites import ralph_site
from ralph.admin.views import RalphDetailView, RalphListView


register = partial(django_register, site=ralph_site)


class WrongViewClassError(Exception):
    pass


class register_extra_view(object):  # noqa
    VIEWS = CHANGE, LIST = ('change', 'list')

    def __init__(self, target_model, target_view):
        if Model not in target_model.__mro__:
            raise ValueError('Model must be a inherited from models.Model.')
        if target_view not in self.VIEWS:
            raise ValueError(
                'The target_view must be a one of '
                'defined choices ({}).'.format(', '.join(self.VIEWS))
            )
        self.target_model = target_model
        self.target_view = target_view

    def __call__(self, view):
        error_msg = '{} must be inherited from {{}}.'.format(view)
        if self.target_view == self.LIST:
            if RalphListView not in view.__mro__:
                raise WrongViewClassError(error_msg.format('RalphListView'))
            signal = admin_get_list_views
        if self.target_view == self.CHANGE:
            if RalphDetailView not in view.__mro__:
                raise WrongViewClassError(error_msg.format('RalphDetailView'))
            signal = admin_get_change_views
        receiver = partial(
            self._add_view, view=view, target_model=self.target_model
        )
        signal.connect(receiver, weak=False)
        return view

    @classmethod
    def _add_view(cls, target_model, model, view, views, **kwargs):
        if target_model == model:
            views.append(view)
