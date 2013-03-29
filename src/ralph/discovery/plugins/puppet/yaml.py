#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


import yaml


def construct_ruby_object(loader, suffix, node):
    return loader.construct_yaml_map(node)


def construct_ruby_sym(loader, node):
    return loader.construct_yaml_str(node)


def load(contents):
    yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
    yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)
    return yaml.load(contents)
