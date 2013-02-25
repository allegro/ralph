# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from ralph.cmdb.models import CI


def update_cis_layers(touched_types, layer_types, layer):
    """
    Update all CIs whose "type" is connected with changed layers.
    """
    ci_objects = CI.objects.filter(type__in=touched_types)
    for ci in ci_objects:
        ci_layers = set()
        for ci_layer in ci.layers.all():
            if ci_layer.id != layer.pk:
                ci_layers.add(ci_layer)
        if ci.type.id in layer_types:
            ci_layers.add(layer)
        ci.layers = ci_layers
        ci.save()
