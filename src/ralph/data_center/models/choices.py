# -*- coding: utf-8 -*-

from dj.choices import Choices


class DataCenterAssetStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    used = _("in use")
    free = _("free")
    damaged = _("damaged")
    liquidated = _("liquidated")
    to_deploy = _("to deploy")
    cleaned = _("cleaned")
    pre_liquidated = _("pre liquidated")


class Orientation(Choices):
    _ = Choices.Choice

    DEPTH = Choices.Group(0)
    front = _("front")
    back = _("back")
    middle = _("middle")

    WIDTH = Choices.Group(100)
    left = _("left")
    right = _("right")

    @classmethod
    def is_width(cls, orientation):
        is_width = orientation in set([choice.id for choice in cls.WIDTH.choices])
        return is_width

    @classmethod
    def is_depth(cls, orientation):
        is_depth = orientation in set([choice.id for choice in cls.DEPTH.choices])
        return is_depth


class RackOrientation(Choices):
    _ = Choices.Choice

    top = _("top")
    bottom = _("bottom")
    left = _("left")
    right = _("right")


class ConnectionType(Choices):
    _ = Choices.Choice

    network = _("network connection")
