# -*- coding: utf-8 -*-

from dj.choices import Choices


class AssetPurpose(Choices):
    _ = Choices.Choice

    for_contractor = _("for contractor")
    sectional = _("sectional")
    for_dashboards = _("for dashboards")
    for_events = _("for events")
    for_tests = _("for tests")
    others = _("others")


class AssetSource(Choices):
    _ = Choices.Choice

    shipment = _("shipment")
    salvaged = _("salvaged")


class ObjectModelType(Choices):
    _ = Choices.Choice

    back_office = _("back office")
    data_center = _("data center")
    part = _("part")
    all = _("all")


class ModelVisualizationLayout(Choices):
    # NOTE: append new layout
    _ = Choices.Choice
    na = _("N/A")
    layout_1x2 = _("1 row x 2 columns").extra(css_class="rows-1 cols-2")
    layout_2x8 = _("2 rows x 8 columns").extra(css_class="rows-2 cols-8")
    layout_2x8AB = _("2 rows x 16 columns (A/B)").extra(
        css_class="rows-2 cols-8 half-slots"
    )
    layout_4x2 = _("4 rows x 2 columns").extra(css_class="rows-4 cols-2")
    layout_2x4 = _("2 rows x 4 columns").extra(css_class="rows-2 cols-4")
    layout_2x2 = _("2 rows x 2 columns").extra(css_class="rows-2 cols-2")
    layout_1x14 = _("1 rows x 14 columns").extra(css_class="rows-1 cols-14")
    layout_2x1 = _("2 rows x 1 columns").extra(css_class="rows-2 cols-1")


class ComponentType(Choices):
    _ = Choices.Choice

    processor = _("processor")
    memory = _("memory")
    disk = _("disk drive")
    ethernet = _("ethernet card")
    expansion = _("expansion card")
    fibre = _("fibre channel card")
    share = _("disk share")
    unknown = _("unknown")
    management = _("management")
    power = _("power module")
    cooling = _("cooling device")
    media = _("media tray")
    chassis = _("chassis")
    backup = _("backup")
    software = _("software")
    os = _("operating system")


class EthernetSpeed(Choices):
    _ = Choices.Choice

    s10mbit = _("10 Mbps")
    s100mbit = _("100 Mbps")
    s1gbit = _("1 Gbps")
    s10gbit = _("10 Gbps")
    s40gbit = _("40 Gbps")
    s100gbit = _("100 Gbps")
    s25gbit = _("25 Gbps")

    UNKNOWN_GROUP = Choices.Group(10)
    unknown = _("unknown speed")


class FibreChannelCardSpeed(Choices):
    _ = Choices.Choice

    s1gbit = _("1 Gbit")
    s2gbit = _("2 Gbit")
    s4gbit = _("4 Gbit")
    s8gbit = _("8 Gbit")
    s16gbit = _("16 Gbit")
    s32gbit = _("32 Gbit")

    UNKNOWN_GROUP = Choices.Group(10)
    unknown = _("unknown speed")
