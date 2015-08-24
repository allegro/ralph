# -*- coding: utf-8 -*-
from ralph.lib.transitions.conf import TRANSITION_ATTR_TAG


def transition_action(func):
    setattr(func, TRANSITION_ATTR_TAG, True)
    return func
