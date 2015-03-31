# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict, Counter

registry = {}
demo_data = defaultdict(dict)


class DemoData(object):
    required = None

    @property
    def name():
        raise NotImplementedError('Please specify name')

    @property
    def title():
        raise NotImplementedError('Please specify title')

    def execute(self):
        print('Create {}.'.format(self.name))
        demo_data[self.name] = self.generate_data(demo_data)
        print('Finish created {}.'.format(self.name))

    def generate_data(self, data):
        raise NotImplementedError('Please override')


class DemoRunner(object):
    """Simple helper class for collection of demo data."""
    def __init__(self, demo_keys, *args, **kwargs):
        self.demo_keys = demo_keys
        super(DemoRunner, self).__init__(*args, **kwargs)

    def run(self):
        """This method find reqiurement of demo data and call execute method
        for each demo in demo_keys."""
        demos = Counter()
        max_depth = 10
        default_weight = 10

        def dig_requirements(demo, depth=1):
            """Method search all requirements for demo and add or update
            weight (count) in demos counter."""
            if max_depth <= depth:
                return
            demos[demo.name] += default_weight * depth
            if demo.required:
                for req in demo.required:
                    dig_requirements(registry[req], depth + 1)

        for key in self.demo_keys:
            dig_requirements(registry[key])
        for key, _ in demos.most_common():
            registry[key]().execute()


def register(demo_klass, **kwargs):
    if demo_klass.name in registry:
        raise NameError('This key ({}) already exist.'.format(demo_klass.name))
    registry[demo_klass.name] = demo_klass
    return demo_klass
