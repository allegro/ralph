# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
import mock

from ralph.discovery.plugins import ssh_ssg
from ralph.discovery.models import DeviceType, IPAddress
from ralph.discovery.tests.util import MockSSH


class SshSsgPluginTest(TestCase):

    def test_ssg(self):
        with mock.patch('ralph.discovery.plugins.ssh_ssg.SSGSSHClient') as SSH:
            SSH.side_effect = MockSSH([
                ('get system', b"""\r
Product Name: SSG-320M\r
Serial Number: JN118F889ADD, Control Number: 00000000\r
Hardware Version: REV 14(0)-(00), FPGA checksum: 00000000, VLAN1 IP (0.0.0.0)\r
Software Version: 6.2.0r10.0, Type: Firewall+VPN\r
Feature: AV-K\r
Compiled by build_master at: Mon Apr 18 20:39:28 PDT 2011\r
Base Mac: b0c6.9a85.9780\r
File Name: ssg320ssg350.6.2.0r10.0, Checksum: 335d2c30\r
, Total Memory: 1023MB\r
\r
Date 07/12/2012 08:25:35, Daylight Saving Time enabled\r
The Network Time Protocol is Enabled\r
Up 912 hours 34 minutes 36 seconds Since 04June2012:07:50:59\r
Total Device Resets: 0\r
\r
System in NAT/route mode.\r
\r
Use interface IP, Config Port: 80\r
Manager IP enforced: False\r
Manager IPs: 8\r
\r
Address                                  Mask                                     Vsys                \r
---------------------------------------- ---------------------------------------- --------------------\r
10.0.0.0                                 255.0.0.0                                Root                \r
172.20.8.0                               255.255.255.0                            Root                \r
172.20.10.0                              255.255.255.0                            Root                \r
91.194.188.61                            255.255.255.255                          Root                \r
91.194.188.90                            255.255.255.255                          Root                \r
91.207.14.90                             255.255.255.255                          Root                \r
91.194.188.58                            255.255.255.255                          Root                \r
172.18.49.0                              255.255.255.0                            Root                \r
User Name: root\r
\r
Interface ethernet0/0(VSI):\r
  description ethernet0/0\r
  number 0, if_info 0, if_index 0, mode route\r
  link up, phy-link up/full-duplex\r
  status change:3, last change:06/04/2012 07:58:00\r
  member of redundant1\r
  vsys Root, zone Untrust, vr trust-vr, vsd 0\r
  admin mtu 0, operating mtu 1500, default mtu 1500\r
  *ip 0.0.0.0/0   mac 0010.dbff.2000\r
  *manage ip 0.0.0.0, mac b0c6.9a85.9780\r
  bandwidth: physical 1000000kbps, configured egress [gbw 0kbps mbw 0kbps]\r
             configured ingress mbw 0kbps, current bw 0kbps\r
             total allocated gbw 0kbps\r
Interface ethernet0/1(VSI):\r
  description ethernet0/1\r
  number 5, if_info 5040, if_index 0, mode nat\r
  link up, phy-link up/full-duplex\r
  status change:3, last change:06/04/2012 07:58:00\r
  vsys Root, zone Trust, vr trust-vr, vsd 0\r
  dhcp client disabled\r
  PPPoE disabled\r
  admin mtu 0, operating mtu 1500, default mtu 1500\r
  *ip 0.0.0.0/0   mac 0010.dbff.2050\r
  *manage ip 0.0.0.0, mac b0c6.9a85.9785\r
  bandwidth: physical 1000000kbps, configured egress [gbw 0kbps mbw 0kbps]\r
             configured ingress mbw 0kbps, current bw 0kbps\r
             total allocated gbw 0kbps\r
Interface ethernet0/2:\r
  description ethernet0/2\r
  number 6, if_info 6048, if_index 0\r
  link up, phy-link up/full-duplex\r
  status change:1, last change:06/04/2012 07:51:16\r
  vsys Root, zone HA, vr trust-vr, vsd 0\r
  *ip 0.0.0.0/0   mac b0c6.9a85.9786\r
  bandwidth: physical 1000000kbps, configured egress [gbw 0kbps mbw 0kbps]\r
             configured ingress mbw 0kbps, current bw 0kbps\r
             total allocated gbw 0kbps\r
Interface ethernet0/3:\r
  description ethernet0/3\r
  number 7, if_info 7056, if_index 0\r
  link up, phy-link up/full-duplex\r
  status change:1, last change:06/04/2012 07:51:16\r
  vsys Root, zone HA, vr trust-vr, vsd 0\r
  *ip 0.0.0.0/0   mac b0c6.9a85.9787\r
  bandwidth: physical 1000000kbps, configured egress [gbw 0kbps mbw 0kbps]\r
             configured ingress mbw 0kbps, current bw 0kbps\r
             total allocated gbw 0kbps\r"""),
            ])
            ssh_ssg.run_ssh_ssg('127.0.0.1')
        ip = IPAddress.objects.get(address='127.0.0.1')
        dev = ip.device
        self.assertNotEquals(dev, None)
        self.assertEqual(dev.model.type, DeviceType.firewall.id)
        self.assertEqual(dev.model.name, 'SSG-320M REV 14(0)-(00)')
        self.assertEqual(dev.sn, 'JN118F889ADD')
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(macs, ['B0C69A859780'])
