import datetime
import re

from dateutil.relativedelta import relativedelta

FILTER_FROM_NOW = re.compile(r'([+-]?\d+)(\w)')


class FilterParser(object):

    def __init__(self, queryset, filters):
        self.queryset = queryset
        self.filters = filters

    def get_queryset(self):
        parsed_filters = {}
        for key, value in self.filters.items():
            params = key.split('|')
            if len(params) == 1:
                parsed_filters[key] = value
            else:
                filter_func = getattr(self, 'filter_' + params[1], None)
                if not filter_func:
                    continue
                parsed_filters[params[0]] = filter_func(value)
        return self.queryset.filter(**parsed_filters)

    def filter_from_now(self, value):
        period_mapper = {
            'd': 'days',
            'm': 'months',
            'y': 'years',
        }
        val, period = FILTER_FROM_NOW.match(value).groups()
        result = datetime.date.today() + relativedelta(**{
            period_mapper.get(period): int(val)
        })
        return result.strftime('%Y-%m-%d')
