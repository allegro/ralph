"""Various utilities for JIRA."""

import json

from restkit import Resource, BasicAuth


class IssueSearch(Resource):
    """Search the issues iterating over single ones, fetching the chunks
    as needed"""

    def __init__(self, jira_url, params, auth=None, **kwargs):
        self.search_url = jira_url
        self.params = params
        filters = []
        if auth is not None:
            filters.append(BasicAuth(*auth))
        super(IssueSearch, self).__init__(
            self.search_url,
            filters=filters,
            follow_redirect=True,
            max_floow_redirect=10,
            **kwargs
        )

    def __iter__(self):
        offset = 0
        total = None
        params = self.params.copy()

        while offset != total:
            params['startAt'] = offset
            resp = self.request('GET', path='/rest/api/2/search/', **params)
            data = json.loads(resp.body_string())
            total = data['total']
            offset += len(data['issues'])
            for issue in data['issues']:
                yield issue
