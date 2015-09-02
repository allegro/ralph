# -*- coding: utf-8 -*-
from functools import partial

from django.contrib.admin.decorators import register as django_register
from django.db.models import Model

from ralph.admin.sites import ralph_site
from ralph.admin.views.extra import (
    CHANGE,
    LIST,
    RalphExtraViewMixin,
    VIEW_TYPES
)

register = partial(django_register, site=ralph_site)


class WrongViewClassError(Exception):
    pass


class register_extra_view(object):  # noqa
    def __init__(self, target_model):
        if Model not in target_model.__mro__:
            raise TypeError('Model must be a inherited from models.Model.')
        self.target_model = target_model

    def __call__(self, view):
        admin_model = ralph_site._registry[self.target_model]
        if not issubclass(view, RalphExtraViewMixin):
            raise ValueError(
                'The view must be inherit from RalphDetailView or RalphListView'
            )
        if view._type not in VIEW_TYPES:
            raise ValueError(
                'The view._type must be a one of '
                'defined choices ({}).'.format(', '.join(VIEW_TYPES))
            )
        if view._type == LIST:
            admin_model.list_views = admin_model.list_views or []
            admin_model.list_views.append(view)
        if view._type == CHANGE:
            admin_model.change_views = admin_model.change_views or []
            admin_model.change_views.append(view)
        view.post_register(ralph_site.name, self.target_model)
        return view
