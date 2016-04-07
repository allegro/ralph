# -*- coding: utf-8 -*-
from django.conf.urls import url

from ralph.api import router
from ralph.lib.transitions.api.views import (
    TransitionActionViewSet,
    TransitionJobViewSet,
    TransitionModelViewSet,
    TransitionView,
    TransitionViewSet
)

router.register(r'transitions', TransitionViewSet)
router.register(r'transitions-action', TransitionActionViewSet)
router.register(r'transitions-model', TransitionModelViewSet)
router.register(r'transitions-job', TransitionJobViewSet)


urlpatterns = [url(
    r'^transition/(?P<transition_pk>[0-9]+)/(?P<obj_pk>\w+)$',
    TransitionView.as_view(),
    name='transition-view'
)]
