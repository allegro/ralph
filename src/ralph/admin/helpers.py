# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse


def get_admin_url(obj, action):
    return reverse(
        "admin:{}_{}_{}".format(
            obj._meta.app_label, obj._meta.model_name, action
        ),
        args=(obj.id,)
    )


def get_field_by_relation_path(model, field_path):
    """
    Returns field for `model` referenced by `field_path`.

    E.g. calling:
        get_field_by_relation_path(BackOfficeAsset, 'model__manufacturer__name')
    returns:
        <django.db.models.fields.CharField: name>
    This is achieved by dynamically executing such code:
        self.model.\
        _meta.get_field('model').related_model.\
        _meta.get_field('manufacturer').related_model.\
        _meta.get_field('name')
    """
    def get_related_model(model, field_name):
        related_model = model._meta.get_field(field_name).related_model
        return related_model

    hops = field_path.split('__')
    relation_hops, dst_field = hops[:-1], hops[-1]
    for field_name in relation_hops:
        model = get_related_model(model, field_name)
    found_field = model._meta.get_field(dst_field)
    return found_field
