"""Various utilities for JIRA."""

import json
import urllib


def iter_issues(url, params):
    """Given an url and parameters iterate over the issues by API. This
    generator will modify the startAt parameter and call the api to receive the
    next chunk of data when necessary."""
    offset = 0
    total = None
    while offset != total:
        params['startAt'] = offset
        f = urllib.urlopen(url + '?' + urllib.urlencode(params))
        data = json.load(f)
        total = data['total']
        offset += len(data['issues'])
        for issue in data['issues']:
            yield issue
