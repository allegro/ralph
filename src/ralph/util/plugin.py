#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


BY_NAME = {}
BY_REQUIREMENTS = {}
PRIORITIES = {}


class Restart(Exception):
    pass


def register(func=None, chain="default", requires=None, priority=None):
    """
    A decorator that registers a function as plugin.
    """

    if func is None:
        def wrapper(f):
            return register(func=f, chain=chain,
                            requires=requires, priority=priority)
        return wrapper
    if not requires:
        requires = set()
    BY_NAME.setdefault(chain, {})[func.func_name] = func
    BY_REQUIREMENTS.setdefault(chain, {}).setdefault(frozenset(requires),
        []).append(func.func_name)
    PRIORITIES.setdefault(chain, {})[func.func_name] = priority or 100
    return func

def next(chain, done_reqs):
    """
    Return a list of plugins that can be run given the list of plugins
    that has already been ran.
    """

    ret = set()
    if chain not in BY_REQUIREMENTS:
        return ret
    done_reqs = set(done_reqs)
    for needed_reqs, plugins in BY_REQUIREMENTS[chain].iteritems():
        if needed_reqs <= done_reqs:
            ret |= set(plugins)
    return ret

def highest_priority(chain, plugins):
    ret = max(plugins, key=lambda p: PRIORITIES.get(chain, {}).get(p, 100))
    return ret

def prioritize(chain, reqs):
    return sorted(reqs, key=lambda p: -PRIORITIES.get(chain, {}).get(p, 100))

def run(chain, func_name, **kwargs):
    """
    Run a plugin by a name.
    """

    return BY_NAME[chain][func_name](**kwargs)


def purge(plugin_set):
    from ralph.util import plugin
    for ck, cv in plugin.BY_REQUIREMENTS.iteritems():
        for pk, pv in cv.iteritems():
            for p in pv:
                if p in plugin_set:
                    plugin_set |= pk
    for ck, cv in plugin.BY_REQUIREMENTS.iteritems():
        for pk, pv in cv.iteritems():
            to_delete = set()
            for p in pv:
                if p not in plugin_set:
                    to_delete.add(p)
            for p in to_delete:
                pv.remove(p)
