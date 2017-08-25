# -*- coding: utf-8 -*-
import logging
import textwrap
import string

from django.conf import settings
from django.core.management.base import BaseCommand

from ralph.dashboards.models import Graph
from ralph.lib.metrics import statsd

logger = logging.getLogger(__name__)
PREFIX = settings.STATSD_GRAPHS_PREFIX
STATSD_PATH = '{}.{{}}.{{}}'.format(PREFIX)


def normalize(s):
    allowed = list(string.ascii_letters + string.digits) + ['_']
    s = s.lower()
    s = s.replace(' ', '_')
    s = s.replace('-', '_')
    return ''.join([c for c in s if c in allowed])


class Command(BaseCommand):

    """Push to statsd data generated by graphs."""
    help = textwrap.dedent(__doc__).strip()

    def handle(self, *args, **kwargs):
        graphs = Graph.objects.filter(push_to_statsd=True)
        for graph in graphs:
            graph_data = graph.get_data()
            graph_name = normalize(graph.name)
            for row in zip(graph_data['labels'], graph_data['series']):
                path = STATSD_PATH.format(graph_name, normalize(row[0]))
                statsd.gauge(path, row[1])
