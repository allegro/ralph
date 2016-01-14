# -*- coding: utf-8 -*-
from django.db import transaction


@transaction.atomic
def move_parents_models(from_obj, to_obj):
    """
    Move parents Django model to diffrent model inheriting from
    the same parent.

    By default Django does not allow the remove of the model without parents.
    Clean _meta.parents, we remove object and add back default parents to class

    Args:
        from_obj: From Django model object
        to_obj: To Django modelo object

    Example:
        >> instance = DataCenterAsset.objects.get(pk=1)
        >> back_office_asset = BackOfficeAsset()
        >> move_parents_models(instance, back_office_asset)
    """
    to_obj.__dict__.update(from_obj.__dict__)
    to_obj.content_type = None
    to_obj.save()
    parents = from_obj._meta.parents
    from_obj._meta.parents = {}
    try:
        from_obj.delete()
    finally:
        from_obj._meta.parents = parents
