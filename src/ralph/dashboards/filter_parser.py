import datetime
import operator
import re
from functools import reduce

from dateutil.relativedelta import relativedelta
from django.db.models import Q

FILTER_FROM_NOW = re.compile(r"([+-]?\d+)(\w)")


class FilterParser(object):
    or_sep = ","

    def __init__(self, queryset, filters_dict, exclude_mode=False):
        self.filters = filters_dict
        if exclude_mode:
            self.queryset_func = queryset.exclude
        else:
            self.queryset_func = queryset.filter

    def get_queryset(self):
        parsed_kwargs = {}
        parsed_args = []
        for key, value in self.filters.items():
            params = key.split("|")
            if len(params) == 1:
                parsed_kwargs[key] = value
            elif len(params) == 2:
                filter_func = getattr(self, "filter_" + params[1], None)
                if not filter_func:
                    continue
                args, kwargs = filter_func(params[0], value)
                parsed_args.extend(args)
                parsed_kwargs.update(kwargs)
            else:
                continue
        return self.queryset_func(*parsed_args, **parsed_kwargs)

    def _filter_operator(self, key, value, op):
        return reduce(op, [Q(**{key: v}) for v in value])

    def filter_or(self, key, value):
        norm_val = value.split(self.or_sep)
        return [self._filter_operator(key, norm_val, operator.or_)], {}

    def filter_and(self, key, value):
        return [self._filter_operator(key, value, operator.and_)], {}

    def filter_from_now(self, key, value):
        period_mapper = {
            "d": "days",
            "m": "months",
            "y": "years",
        }
        val, period = FILTER_FROM_NOW.match(value).groups()
        result = datetime.date.today() + relativedelta(
            **{period_mapper.get(period): int(val)}
        )
        return [], {key: result.strftime("%Y-%m-%d")}
