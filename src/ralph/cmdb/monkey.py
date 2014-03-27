#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tastypie import http
from tastypie.exceptions import ImmediateHttpResponse, HttpResponse


def method_check(self, request, allowed=None):
    if allowed is None:
        allowed = []
    request_method = request.method.lower()
    allows = ','.join(map(lambda x: x.upper(), allowed))
    if request_method == "options":
        response = HttpResponse(allows)
        response['Allow'] = allows
        raise ImmediateHttpResponse(response=response)

    if request_method not in allowed:
        response = http.HttpMethodNotAllowed(allows)
        response['Allow'] = allows
        raise ImmediateHttpResponse(response=response)

    return request_method
