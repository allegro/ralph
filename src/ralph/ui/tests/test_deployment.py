# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
from django import forms

from ralph.discovery.models import (
    Network,
    DataCenter,
    Device,
    DeviceType,
    DiskShare,
    DiskShareMount,
    IPAddress,
)
from ralph.business.models import Venture, VentureRole
from ralph.deployment.models import Preboot, Deployment
from ralph.ui.forms import (
    _validate_cols_count,
    _validate_cols_not_empty,
    _validate_mac,
    _validate_management_ip,
    _validate_network_name,
    _validate_venture_and_role,
    _validate_preboot,
    _validate_deploy_children,
    _validate_hostname,
    _validate_ip_address,
    _validate_ip_owner,
)


class BulkDeploymentTest(TestCase):
    def test_validate_cols_count(self):
        with self.assertRaises(forms.ValidationError):
            _validate_cols_count(1, [1, 2], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_cols_count(3, [1, 2], 0)
        _validate_cols_count(2, [1, 2], 0)

    def test_validate_cols_not_empty(self):
        with self.assertRaises(forms.ValidationError):
            _validate_cols_not_empty(['splorf', ''], 0)
        _validate_cols_not_empty([], 0)
        _validate_cols_not_empty(['bonk', 'whack', 'thud'], 0)

    def test_validate_mac(self):
        _validate_mac('deadbeefcafe', [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_mac('deadbeefcafe', ['deadbeefcafe'], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_mac('sproing', ['deadbeefcafe'], 0)

    def test_valdate_management_ip(self):
        _validate_management_ip('127.0.0.1', [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_management_ip('127.0.0.0.1', [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_management_ip('127.0.0.1', ['127.0.0.1'], 0)

    def test_validate_network_name(self):
        with self.assertRaises(forms.ValidationError):
            _validate_network_name('wroom', 0)
        dc = DataCenter(name='dc')
        dc.save()
        Network(name='wroom', address='127.0.0.1/24', data_center=dc).save()
        _validate_network_name('wroom', 0)

    def test_validate_venture_and_role(self):
        with self.assertRaises(forms.ValidationError):
            _validate_venture_and_role('bang', 'klang', 0)
        v = Venture(name='Bang', symbol='bang')
        v.save()
        with self.assertRaises(forms.ValidationError):
            _validate_venture_and_role('bang', 'klang', 0)
        r = VentureRole(name='klang', venture=v)
        r.save()
        _validate_venture_and_role('bang', 'klang', 0)
        # FIXME This should also work!
        # VentureRole(name='zing', venture=v, parent=r).save()
        # _validate_venture_and_role('bang', 'klang/zing', 0)

    def test_validate_preboot(self):
        with self.assertRaises(forms.ValidationError):
            _validate_preboot('bazinga', 0)
        Preboot(name='bazinga').save()
        _validate_preboot('bazinga', 0)

    def test_validate_deploy_children(self):
        _validate_deploy_children('deadbeefcafe', 0)
        parent = Device.create(
            ethernets=[('', 'deadbeefcafe', 0)],
            model_name='splat',
            model_type=DeviceType.unknown,
        )
        _validate_deploy_children('deadbeefcafe', 0)
        device = Device.create(
            ethernets=[('', 'cafedeadbeef', 0)],
            model_name='splat',
            model_type=DeviceType.unknown,
            parent=parent,
        )
        with self.assertRaises(forms.ValidationError):
            _validate_deploy_children('deadbeefcafe', 0)
        device.parent = None
        device.save()
        _validate_deploy_children('deadbeefcafe', 0)
        _validate_deploy_children('cafedeadbeef', 0)
        share = DiskShare(wwn='a' * 33, device=parent)
        share.save()
        mount = DiskShareMount(share=share, device=device, server=device)
        mount.save()
        with self.assertRaises(forms.ValidationError):
            _validate_deploy_children('deadbeefcafe', 0)
        with self.assertRaises(forms.ValidationError):
            _validate_deploy_children('cafedeadbeef', 0)

    def test_validate_hostname(self):
        _validate_hostname('whoosh', [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_hostname('whoosh', ['whoosh'], 0)
        device = Device.create(
            ethernets=[('', 'deadbeefcafe', 0)],
            model_name='splat',
            model_type=DeviceType.unknown,
        )
        Deployment(
            hostname='whoosh',
            ip='127.0.0.1',
            mac='deadbeefcafe',
            device=device,
            preboot=None,
            venture=None,
            venture_role=None,
        ).save()
        with self.assertRaises(forms.ValidationError):
            _validate_hostname('whoosh', [], 0)

    def test_validate_ip_address(self):
        dc = DataCenter(name='dc')
        dc.save()
        net = Network(
            name='wroom',
            address='127.0.0.1/24',
            data_center=dc
        )
        net.save()
        _validate_ip_address('127.0.0.1', net, [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_ip_address('127.0.0.1/24', net, [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_ip_address('127.1.0.1', net, [], 0)
        with self.assertRaises(forms.ValidationError):
            _validate_ip_address('127.0.0.1', net, ['127.0.0.1'], 0)

    def test_validate_ip_owner(self):
        _validate_ip_owner('127.0.0.1', 'deadbeefcafe', 0)
        ip = IPAddress(address='127.0.0.1')
        ip.save()
        with self.assertRaises(forms.ValidationError):
            _validate_ip_owner('127.0.0.1', 'deadbeefcafe', 0)
        ip.device = Device.create(
            ethernets=[('', 'deadbeefcafe', 0)],
            model_name='splat',
            model_type=DeviceType.unknown,
        )
        ip.device.save()
        ip.save()
        _validate_ip_owner('127.0.0.1', 'deadbeefcafe', 0)
        ip.device = None
        ip.save()
        with self.assertRaises(forms.ValidationError):
            _validate_ip_owner('127.0.0.1', 'deadbeefcafe', 0)

