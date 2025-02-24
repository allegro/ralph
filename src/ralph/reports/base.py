# -*- coding: utf-8 -*-
import uuid


class ReportNode(object):
    """The basic report node. It is simple object which store name, count,
    parent and children."""

    def __init__(self, name, count=0, parent=None, children=[], link=None, **kwargs):
        self.name = name
        self.count = count
        self.parent = parent
        self.children = []
        self.link = link
        self.uid = "n{}".format(uuid.uuid1())

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_to_count(self, count):
        self.count += count

    def update_count(self):
        for node in self.ancestors:
            node.add_to_count(self.count)

    @property
    def ancestors(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def to_dict(self):
        return {
            "name": self.name,
            "count": self.count,
        }

    def __str__(self):
        return "{} ({})".format(self.name, self.count)


class ReportContainer(list):
    """Container for nodes. This class provides few helpful methods to
    manipulate on node set."""

    def get(self, name):
        return next((node for node in self if node.name == name), None)

    def get_or_create(self, name):
        node = self.get(name)
        created = False
        if not node:
            node = ReportNode(name)
            self.append(node)
            created = True
        return node, created

    def add(self, name, count=0, parent=None, unique=True, link=None):
        if unique:
            new_node, created = self.get_or_create(name)
        else:
            new_node = ReportNode(name)
            self.append(new_node)
            created = True
        new_node.count = count
        if parent:
            if not isinstance(parent, ReportNode):
                parent, __ = self.get_or_create(parent)
        if created:
            parent.add_child(new_node)
        new_node.link = link
        return new_node, parent

    @property
    def roots(self):
        return [node for node in self if node.parent is None]

    @property
    def leaves(self):
        return [node for node in self if node.children == []]

    def to_dict(self):
        def traverse(node):
            ret = node.to_dict()
            ret["children"] = []
            for child in node.children:
                ret["children"].append(traverse(child))
            return ret

        return [traverse(root) for root in self.roots]
