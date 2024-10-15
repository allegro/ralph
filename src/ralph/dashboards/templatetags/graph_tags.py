# -*- coding: utf-8 -*-
from django.template import Library

register = Library()


@register.inclusion_tag("dashboard/templatetags/render_graph.html")
def render_graph(graph):
    return {"graph": graph}
