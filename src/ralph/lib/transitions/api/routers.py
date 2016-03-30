# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.api import router
from ralph.lib.transitions.api.views import (
    TransitionActionViewSet,
    TransitionModelViewSet,
    TransitionView,
    TransitionViewSet
)

router.register(r'transitions', TransitionViewSet)
router.register(r'transitions-action', TransitionActionViewSet)
router.register(r'transitions-model', TransitionModelViewSet)


urlpatterns = [url(
    r'^transition/(?P<transition_id>[0-9]+)/(?P<obj_pk>[0-9]+)$',
    TransitionView.as_view(),
    name='transition-view'
)]
