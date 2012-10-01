#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.utils.datastructures import MultiValueDict


def get_indent(line):
    for indent, c in enumerate(line):
        if c not in ' \t\r\n\v':
            return indent
    return len(line)

def pairs(text='', lines=None):
    r"""
        Parse nested key-value pairs as returned by ipmitool.

        >>> pairs('abc: def\n ghi: jkl\n mno: pqr')
        {u'def': {None: u'abc', u'ghi': u'jkl', u'mno': u'pqr'}}
    """

    if lines is None:
        lines = text.splitlines()
    last_indent = 0
    root = {}
    parents = [root]
    last_key = None
    for line in lines:
        if not line.strip():
            continue
        if ':' in line:
            key, value = (v.strip() for v in line.split(':', 1))
        else:
            key = line.strip()
            value = key
        indent = get_indent(line)
        if indent < last_indent:
            parents.pop()
        elif indent > last_indent:
            last_value = parents[-1][last_key]
            last_node = {None: last_key}
            del parents[-1][last_key]
            parents[-1][last_value] = last_node
            parents.append(last_node)
        parents[-1][key] = value
        last_indent = indent
        last_key = key
    return root

def multi_pairs(text='', lines=None):
    r"""
        Parse nested key-value pairs with repetitions.

        >>> pairs('abc: def\n ghi: jkl\n mno: pqr')
        {u'def': {None: u'abc', u'ghi': u'jkl', u'mno': u'pqr'}}
    """

    if lines is None:
        lines = text.splitlines()
    root = MultiValueDict()
    parents = [root]
    indents = [0]
    last_key = None
    for line in lines:
        if not line.strip():
            continue
        if ':' in line:
            key, value = (v.strip() for v in line.split(':', 1))
        else:
            key = line.strip()
            value = None
        indent = get_indent(line)
        while indent < indents[-1]:
            indents.pop()
            parents.pop()
        if indent > indents[-1]:
            node = MultiValueDict()
            parents[-1].appendlist(last_key, node)
            parents.append(node)
            indents.append(indent)
        parents[-1].appendlist(key, value)
        last_key = key
    return root


def tree(text='', lines=None):
    r"""
        Parse a nested tree of targets.

        >>> tree('1\n    1.1\n    1.2\n2\n    2.1')
        {u'1': {u'1.1': {}, u'1.2': {}}, u'2': {u'2.1': {}}}
    """
    if lines is None:
        lines = text.splitlines()
    levels = { -1: {} }
    for line in lines:
        if not line.strip():
            continue
        key = line.strip()
        indent = get_indent(line)
        node = {}
        for i, n in reversed(sorted(levels.iteritems())):
            if indent > i:
                n[key] = node
                break
        levels[indent] = node
    return levels[-1]
