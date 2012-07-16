#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import functools
import cStringIO as StringIO

from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json

from ralph.util import csvutil


def jsonify(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        reply = func(*args, **kwargs)
        if isinstance(reply, HttpResponseRedirect):
            return reply
        return HttpResponse(json.dumps(reply),
                            mimetype="application/javascript")
    return wrapper

def csvify(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        reply = func(*args, **kwargs)
        if isinstance(reply, HttpResponseRedirect):
            return reply
        f = StringIO.StringIO()
        csvutil.UnicodeWriter(f).writerows(reply)
        return HttpResponse(f.getvalue(), mimetype="application/csv")
    return wrapper

