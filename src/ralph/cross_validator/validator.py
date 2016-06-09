from django.core.exceptions import ObjectDoesNotExist

from ralph.cross_validator.helpers import get_imported_obj, get_obj_id_ralph_20, diff
from ralph.cross_validator.models import Result, Run
from ralph.cross_validator.ralph2.device import old_asset_dict


def check_objects(qs):
    run = Run.objects.create()
    invalid_count, valid_count = 0, 0
    for obj in qs:
        result, errors = check_object(obj=obj, run=run)
        if errors or bool(result):
            invalid_count += 1
        else:
            valid_count += 1
    run.invalid_count = invalid_count
    run.valid_count = valid_count
    run.save()


def check_object(obj, run=None):
    imported_object = get_imported_obj(obj)
    errors = []
    old_obj = None
    try:
        old_obj = old_asset_dict(old_id=get_obj_id_ralph_20(imported_object))
    except ObjectDoesNotExist:
        pass
        # errors.append('ObjectDoesNotExist')
    result = diff(
        old=old_obj,
        new=obj.__dict__,
        blacklist=['id', 'parent_id']
    )
    result = list(result)
    if run and (errors or result):
        Result.create(
            run=run,
            obj=obj,
            old=imported_object,
            result=result,
            errors=errors
        )
    return result, errors
