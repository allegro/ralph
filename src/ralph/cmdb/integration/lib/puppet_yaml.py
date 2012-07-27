#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import yaml

class PuppetReport(yaml.YAMLObject):
  yaml_tag = u'!ruby/object:Puppet::Transaction::Report'
  def __init__(self, host, logs, metrics, records, time, resource_statuses):
    self.host = host
    self.logs = logs
    self.metrics = metrics
    self.resource_statuses = resource_statuses
    self.records = records
    self.time = time

class PuppetResourceStatus(yaml.YAMLObject):
    yaml_tag=u'!ruby/object:Puppet::Resource::Status'
    def __init__(self, *args, **kwargs):
        pass

class PuppetLog(yaml.YAMLObject):
    yaml_tag = u'!ruby/object:Puppet::Util::Log'
    def __init__(self, source, message, tags, time, level):
        self.source = source
        self.message = message
        self.tags = tags
        self.time = time
        self.level = level

class PuppetMetric(yaml.YAMLObject):
    yaml_tag = u'!ruby/object:Puppet::Util::Metric'
    def __init__(self, values, name, label):
        self.values = values
        self.name = name
        self.label = label

class PuppetTransactionEvent(yaml.YAMLObject):
    yaml_tag=u"!ruby/object:Puppet::Transaction::Event"

def construct_ruby_object(loader, suffix, node):
    return loader.construct_yaml_map(node)

def construct_ruby_sym(loader, node):
    return loader.construct_yaml_str(node)

def load(contents):
    #example
    yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
    yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)
    stream = contents
    mydata = yaml.load(stream)
    return mydata
