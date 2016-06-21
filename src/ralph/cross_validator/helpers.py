from django.contrib.contenttypes.models import ContentType

from ralph.data_importer.models import ImportedObjects


def get_fields(obj):
    """
    Return object fields names excluding excluded ones.
    """
    return set(
        obj._meta.get_all_field_names()
    ) - set(
        getattr(obj, '_excludes', [])
    )


def get_fitered_dict(obj):
    """
    Filter obj dict (__dict__) to fetch only model fields
    """
    fields = get_fields(obj)
    return {k: v for k, v in obj.__dict__.items() if k in fields}


def get_imported_obj(obj):
    """
    Return ImportedObject for passed object.
    """
    if not obj:
        return None
    content_type = ContentType.objects.get_for_model(obj._meta.model)
    try:
        imported_obj = ImportedObjects.objects.get(
            object_pk=obj.pk,
            content_type=content_type,
        )
    except (obj._meta.model.DoesNotExist, ImportedObjects.DoesNotExist):
        return None
    return imported_obj


def get_obj_id_ralph_20(obj):
    """
    Returns ID of object in Ralph2 or None if not found.
    """
    if isinstance(obj, ImportedObjects):
        return obj.old_object_pk
    imported_obj = get_imported_obj(obj)
    return imported_obj.old_object_pk if imported_obj else None


def normalize(value):
    """
    Normalize diff value (ex. '' is equal to None).
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
    if value == '':
        return None
    return value


def diff(old, new, blacklist=None):
    """
    Create diff between old and new objects.

    Args:
        old: dict of old values
        new: dict of new values
        blacklist: list of blacklisted fields (keys)
    """
    if old is None:
        old = {}
    common_keys = set(old.keys()).intersection(set(new.keys()))
    common_keys -= set(blacklist) if blacklist else set()
    for change in common_keys:
        old_value = normalize(old[change])
        new_value = normalize(new[change])
        if old_value != new_value:
            yield change, old_value, new_value
