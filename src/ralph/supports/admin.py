# -*- coding: utf-8 -*-
import reversion

from django.contrib import admin
from django.db import models

from ralph.supports import models as models_supports

# ugly automagical register base admin for each model
for model in models_supports.__dict__.values():
    try:
        mro = model.__mro__
    except AttributeError:
        pass
    else:
        if models.Model in mro and not model._meta.abstract:
            @admin.register(model)
            class ModelAdmin(reversion.VersionAdmin):
                pass
