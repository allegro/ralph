# -*- coding: utf-8 -*-
import django.dispatch

post_transition = django.dispatch.Signal(["user", "assets", "transition"])
