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

    shipment = _('shipment')
    salvaged = _('salvaged')


class ObjectModelType(Choices):
    _ = Choices.Choice

    back_office = _('back office')
    data_center = _('data center')
    part = _('part')
    all = _('all')


class ModelVisualizationLayout(Choices):
    _ = Choices.Choice

    na = _('N/A')
    layout_1x2 = _('1x2').extra(css_class='rows-1 cols-2')
    layout_2x8 = _('2x8').extra(css_class='rows-2 cols-8')
    layout_2x8AB = _('2x16 (A/B)').extra(css_class='rows-2 cols-8 half-slots')
    layout_4x2 = _('4x2').extra(css_class='rows-4 cols-2')


class ComponentType(Choices):
    _ = Choices.Choice

    processor = _('processor')
    memory = _('memory')
    disk = _('disk drive')
    ethernet = _('ethernet card')
    expansion = _('expansion card')
    fibre = _('fibre channel card')
    share = _('disk share')
    unknown = _('unknown')
    management = _('management')
    power = _('power module')
    cooling = _('cooling device')
    media = _('media tray')
    chassis = _('chassis')
    backup = _('backup')
    software = _('software')
    os = _('operating system')
