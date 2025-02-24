# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.api import router
from ralph.lib.transitions.api.views import (
    AvailableTransitionViewSet,
    TransitionActionViewSet,
    TransitionByIdView,
    TransitionJobViewSet,
    TransitionModelViewSet,
    TransitionsHistoryViewSet,
    TransitionView,
    TransitionViewSet
)

router.register(r'transitions', TransitionViewSet)
router.register(r'transitions-action', TransitionActionViewSet)
router.register(r'transitions-model', TransitionModelViewSet)
router.register(r'transitions-job', TransitionJobViewSet)
router.register(r'transitions-history', TransitionsHistoryViewSet)

router.register(
    r'(?P<app_label>\w+)/(?P<model>\w+)/(?P<obj_pk>\w+)/transitions',
    AvailableTransitionViewSet,
    basename='available-transiton'
)

urlpatterns = [
    # Deprecated
    url(
        r'^transition/(?P<transition_pk>[0-9]+)/(?P<obj_pk>\w+)$',
        TransitionByIdView.as_view(),
        name='transition-view'
    ),
    url(
        r'^transitions/(?P<transition_pk>[0-9]+)/(?P<obj_pk>\w+)$',
        TransitionByIdView.as_view(),
        name='transitions-view'
    ),
    url(
        r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<obj_pk>[0-9]+)/transitions/(?P<transition_pk>[0-9]+)/$',  # noqa
        TransitionView.as_view(),
        name='transitions-by-id-view'
    ),
    url(
        r'^(?P<app_label>\w+)/(?P<model>\w+)/(?P<obj_pk>[0-9]+)/transitions/(?P<transition_name>[\w ]+)/$',  # noqa
        TransitionView.as_view(),
        name='transitions-by-name-view'
    )
]
