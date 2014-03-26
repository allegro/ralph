# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase
import mock

from ralph.discovery.plugins import ssh_aix
from ralph.discovery.models import (DeviceType, Device, IPAddress, DiskShare,
                                    OperatingSystem)

from ralph.discovery.tests.util import MockSSH


class SshAixPluginTest(TestCase):

    def setUp(self):
        ip = IPAddress(address='127.0.0.1')
        ip.snmp_name = 'IBM PowerPC CHRP Computer'
        ip.snmp_community = 'public'
        ip.snmp_version = '2c'
        ip.save()
        self.ip = ip
        self.kwargs = {
            'ip': ip.address,
            'community': ip.snmp_community,
            'snmp_name': ip.snmp_name,
            'snmp_version': ip.snmp_version,
        }
        dev = Device.create(sn='foo', model_type=DeviceType.storage,
                            model_name='foo')
        dev.save()
        self.share = DiskShare(wwn='2AC000250A9B5000', device=dev)
        self.share.save()

    def tearDown(self):
        self.ip.delete()
        self.share.delete()

    def test_aix(self):
        with mock.patch('ralph.discovery.plugins.ssh_aix._connect_ssh') as SSH:
            SSH.side_effect = MockSSH([
                (u'lsattr -El sys0 | grep ^modelname',
                 u'modelname       IBM,8233-E8B       Machine name                                      False\n'),
                (u'netstat -ia | grep link',
                 u'en0   9000  link#2      0.21.5e.e2.1b.50 576634574     0 573329335     0     0\nen1   9000  link#3      0.21.5e.e2.1b.52 576760839     0 572772320     0     0\nen2   9000  link#4      0.21.5e.e2.18.98 576767812     0 573362079     0     0\nen3   9000  link#5      0.21.5e.e2.18.9a 576726865     0 572257966     0     0\nen6   9000  link#6      0.21.5e.e2.2d.e0    93594     0  1209927     0     0\nen7   9000  link#7      0.21.5e.e2.2d.e2   100896     0  1202620     0     0\nen8   1500  link#8      e4.1f.13.4e.7e.8e 139058659     0 1505805421     6     0\nlo0   16896 link#1                       2342682952     0 2343897647     0     0\n'),
                (u'lsdev -c disk',
                 u'hdisk0  Available 04-08-00 SAS Disk Drive\nhdisk1  Available 04-08-00 SAS Disk Drive\nhdisk2  Available 04-08-00 SAS Disk Drive\nhdisk3  Available 04-08-00 SAS Disk Drive\nhdisk4  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk5  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk6  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk7  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk8  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk9  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk10 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk11 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk12 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk13 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk14 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk15 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk16 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk17 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk18 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk19 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk20 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk21 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk22 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk23 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk24 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk25 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk26 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk27 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk28 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk29 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk30 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk31 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk32 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk33 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk34 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk35 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk36 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk37 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk38 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk39 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk40 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk41 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk42 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk43 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk44 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk45 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk46 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk47 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk48 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk49 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk50 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk51 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk52 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk53 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk54 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk55 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk56 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk57 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk58 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk59 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk60 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk61 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk62 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk63 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk64 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk65 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk66 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk67 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk68 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk69 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk70 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk71 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk72 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk73 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk74 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk75 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk76 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk77 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk78 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk79 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk80 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk81 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk82 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk83 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk84 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk85 Available 08-00-02 3PAR InServ Virtual Volume\n'),
                (u'lscfg -vl hdisk0',
                 u'  hdisk0           U78A0.001.DNWK041-P2-D3  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RKYY\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F003002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D3\n\n'),
                (u'lscfg -vl hdisk1',
                 u'  hdisk1           U78A0.001.DNWK041-P2-D4  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RJQ2\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F001002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D4\n\n'),
                (u'lscfg -vl hdisk2',
                 u'  hdisk2           U78A0.001.DNWK041-P2-D5  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RJZS\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F003002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D5\n\n'),
                (u'lscfg -vl hdisk3',
                 u'  hdisk3           U78A0.001.DNWK041-P2-D6  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RKYZ\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F001002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D6\n\n'),
                (u'lscfg -vl hdisk4',
                 u'  hdisk4           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L0  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000090A9B5000\n\n'),
                (u'lscfg -vl hdisk5',
                 u'  hdisk5           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L1000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000A0A9B5000\n\n'),
                (u'lscfg -vl hdisk6',
                 u'  hdisk6           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000B0A9B5000\n\n'),
                (u'lscfg -vl hdisk7',
                 u'  hdisk7           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000C0A9B5000\n\n'),
                (u'lscfg -vl hdisk8',
                 u'  hdisk8           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000D0A9B5000\n\n'),
                (u'lscfg -vl hdisk9',
                 u'  hdisk9           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L14000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000F0A9B5000\n\n'),
                (u'lscfg -vl hdisk10',
                 u'  hdisk10          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000100A9B5000\n\n'),
                (u'lscfg -vl hdisk11',
                 u'  hdisk11          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L16000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000110A9B5000\n\n'),
                (u'lscfg -vl hdisk12',
                 u'  hdisk12          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L17000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000120A9B5000\n\n'),
                (u'lscfg -vl hdisk13',
                 u'  hdisk13          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L28000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000130A9B5000\n\n'),
                (u'lscfg -vl hdisk14',
                 u'  hdisk14          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L29000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000140A9B5000\n\n'),
                (u'lscfg -vl hdisk15',
                 u'  hdisk15          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L2A000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000150A9B5000\n\n'),
                (u'lscfg -vl hdisk16',
                 u'  hdisk16          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L2B000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000160A9B5000\n\n'),
                (u'lscfg -vl hdisk17',
                 u'  hdisk17          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000170A9B5000\n\n'),
                (u'lscfg -vl hdisk18',
                 u'  hdisk18          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000180A9B5000\n\n'),
                (u'lscfg -vl hdisk19',
                 u'  hdisk19          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000190A9B5000\n\n'),
                (u'lscfg -vl hdisk20',
                 u'  hdisk20          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001A0A9B5000\n\n'),
                (u'lscfg -vl hdisk21',
                 u'  hdisk21          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L50000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001B0A9B5000\n\n'),
                (u'lscfg -vl hdisk22',
                 u'  hdisk22          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L51000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001C0A9B5000\n\n'),
                (u'lscfg -vl hdisk23',
                 u'  hdisk23          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L52000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001D0A9B5000\n\n'),
                (u'lscfg -vl hdisk24',
                 u'  hdisk24          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L53000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001E0A9B5000\n\n'),
                (u'lscfg -vl hdisk25',
                 u'  hdisk25          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L64000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001F0A9B5000\n\n'),
                (u'lscfg -vl hdisk26',
                 u'  hdisk26          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L65000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000200A9B5000\n\n'),
                (u'lscfg -vl hdisk27',
                 u'  hdisk27          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L66000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000210A9B5000\n\n'),
                (u'lscfg -vl hdisk28',
                 u'  hdisk28          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L67000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000220A9B5000\n\n'),
                (u'lscfg -vl hdisk29',
                 u'  hdisk29          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L68000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000230A9B5000\n\n'),
                (u'lscfg -vl hdisk30',
                 u'  hdisk30          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L69000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000240A9B5000\n\n'),
                (u'lscfg -vl hdisk31',
                 u'  hdisk31          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L96000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002D0A9B5000\n\n'),
                (u'lscfg -vl hdisk32',
                 u'  hdisk32          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L97000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002E0A9B5000\n\n'),
                (u'lscfg -vl hdisk33',
                 u'  hdisk33          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L98000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002F0A9B5000\n\n'),
                (u'lscfg -vl hdisk34',
                 u'  hdisk34          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L99000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000300A9B5000\n\n'),
                (u'lscfg -vl hdisk35',
                 u'  hdisk35          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9A000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000310A9B5000\n\n'),
                (u'lscfg -vl hdisk36',
                 u'  hdisk36          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9B000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000320A9B5000\n\n'),
                (u'lscfg -vl hdisk37',
                 u'  hdisk37          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000330A9B5000\n\n'),
                (u'lscfg -vl hdisk38',
                 u'  hdisk38          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000340A9B5000\n\n'),
                (u'lscfg -vl hdisk39',
                 u'  hdisk39          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC8000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000250A9B5000\n\n'),
                (u'lscfg -vl hdisk40',
                 u'  hdisk40          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC9000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000260A9B5000\n\n'),
                (u'lscfg -vl hdisk41',
                 u'  hdisk41          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000270A9B5000\n\n'),
                (u'lscfg -vl hdisk42',
                 u'  hdisk42          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000280A9B5000\n\n'),
                (u'lscfg -vl hdisk43',
                 u'  hdisk43          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000290A9B5000\n\n'),
                (u'lscfg -vl hdisk44',
                 u'  hdisk44          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCD000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002A0A9B5000\n\n'),
                (u'lscfg -vl hdisk45',
                 u'  hdisk45          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCE000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002B0A9B5000\n\n'),
                (u'lscfg -vl hdisk46',
                 u'  hdisk46          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCF000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002C0A9B5000\n\n'),
                (u'lscfg -vl hdisk47',
                 u'  hdisk47          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000350A9B5000\n\n'),
                (u'lscfg -vl hdisk48',
                 u'  hdisk48          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000360A9B5000\n\n'),
                (u'lscfg -vl hdisk49',
                 u'  hdisk49          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000370A9B5000\n\n'),
                (u'lscfg -vl hdisk50',
                 u'  hdisk50          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFD000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000380A9B5000\n\n'),
                (u'lscfg -vl hdisk51',
                 u'  hdisk51          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFE000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000390A9B5000\n\n'),
                (u'lscfg -vl hdisk52',
                 u'  hdisk52          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFF000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003A0A9B5000\n\n'),
                (u'lscfg -vl hdisk53',
                 u'  hdisk53          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000470A9B5000\n\n'),
                (u'lscfg -vl hdisk54',
                 u'  hdisk54          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000480A9B5000\n\n'),
                (u'lscfg -vl hdisk55',
                 u'  hdisk55          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000490A9B5000\n\n'),
                (u'lscfg -vl hdisk56',
                 u'  hdisk56          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004A0A9B5000\n\n'),
                (u'lscfg -vl hdisk57',
                 u'  hdisk57          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L130000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004B0A9B5000\n\n'),
                (u'lscfg -vl hdisk58',
                 u'  hdisk58          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L131000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004C0A9B5000\n\n'),
                (u'lscfg -vl hdisk59',
                 u'  hdisk59          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L132000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004D0A9B5000\n\n'),
                (u'lscfg -vl hdisk60',
                 u'  hdisk60          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L133000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004E0A9B5000\n\n'),
                (u'lscfg -vl hdisk61',
                 u'  hdisk61          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L134000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004F0A9B5000\n\n'),
                (u'lscfg -vl hdisk62',
                 u'  hdisk62          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L135000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000500A9B5000\n\n'),
                (u'lscfg -vl hdisk63',
                 u'  hdisk63          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L136000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000510A9B5000\n\n'),
                (u'lscfg -vl hdisk64',
                 u'  hdisk64          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L137000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000520A9B5000\n\n'),
                (u'lscfg -vl hdisk65',
                 u'  hdisk65          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C60A9B5000\n\n'),
                (u'lscfg -vl hdisk66',
                 u'  hdisk66          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003B0A9B5000\n\n'),
                (u'lscfg -vl hdisk67',
                 u'  hdisk67          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003C0A9B5000\n\n'),
                (u'lscfg -vl hdisk68',
                 u'  hdisk68          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L160000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003D0A9B5000\n\n'),
                (u'lscfg -vl hdisk69',
                 u'  hdisk69          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L161000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003E0A9B5000\n\n'),
                (u'lscfg -vl hdisk70',
                 u'  hdisk70          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L162000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003F0A9B5000\n\n'),
                (u'lscfg -vl hdisk71',
                 u'  hdisk71          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L163000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000400A9B5000\n\n'),
                (u'lscfg -vl hdisk72',
                 u'  hdisk72          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L164000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000410A9B5000\n\n'),
                (u'lscfg -vl hdisk73',
                 u'  hdisk73          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L165000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000420A9B5000\n\n'),
                (u'lscfg -vl hdisk74',
                 u'  hdisk74          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L166000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000430A9B5000\n\n'),
                (u'lscfg -vl hdisk75',
                 u'  hdisk75          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L167000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000440A9B5000\n\n'),
                (u'lscfg -vl hdisk76',
                 u'  hdisk76          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L169000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000460A9B5000\n\n'),
                (u'lscfg -vl hdisk77',
                 u'  hdisk77          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L190000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000530A9B5000\n\n'),
                (u'lscfg -vl hdisk78',
                 u'  hdisk78          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L191000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000540A9B5000\n\n'),
                (u'lscfg -vl hdisk79',
                 u'  hdisk79          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L5000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C10A9B5000\n\n'),
                (u'lscfg -vl hdisk80',
                 u'  hdisk80          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L40000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C20A9B5000\n\n'),
                (u'lscfg -vl hdisk81',
                 u'  hdisk81          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L41000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C30A9B5000\n\n'),
                (u'lscfg -vl hdisk82',
                 u'  hdisk82          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L192000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C40A9B5000\n\n'),
                (u'lscfg -vl hdisk83',
                 u'  hdisk83          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L138000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C50A9B5000\n\n'),
                (u'lscfg -vl hdisk84',
                 u'  hdisk84          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L168000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000450A9B5000\n\n'),
                (u'lscfg -vl hdisk85',
                 u'  hdisk85          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000CE0A9B5000\n\n'),
                (u'oslevel', u'5.3.0.0\n'),
                (u'lsattr -El sys0 | grep ^realmem',
                 u'realmem      4194304       Amount of usable physical memory in Kbytes        False\n'),
                (u'lparstat -i|grep ^Active\ Phys',
                 u'Active Physical CPUs in system             : 8\n'),
            ])
            ssh_aix.run_ssh_aix('127.0.0.1')
        ip = IPAddress.objects.get(address='127.0.0.1')
        dev = ip.device
        self.assertNotEquals(dev, None)
        self.assertEquals(dev.model.type, DeviceType.rack_server.id)
        self.assertEquals(dev.model.name, 'IBM Power 750 Express AIX')
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(
            macs,
            ['00215EE21898', '00215EE2189A', '00215EE21B50', '00215EE21B52',
             '00215EE22DE0', '00215EE22DE2', 'E41F134E7E8E'])
        mounts = [m.share.wwn for m in dev.disksharemount_set.all()]
        self.assertEquals(mounts, ['2AC000250A9B5000'])
        disks = [s.sn for s in dev.storage_set.all()]
        self.assertEquals(
            disks, ['3TB1RJQ2', '3TB1RJZS', '3TB1RKYY', '3TB1RKYZ'])
        os = None
        try:
            os = OperatingSystem.objects.get(device=dev)
        except OperatingSystem.DoesNotExist:
            pass
        self.assertNotEquals(os, None)
        self.assertEquals(os.label, 'AIX 5.3.0.0')
        self.assertEquals(os.memory, 4096)
        self.assertEquals(os.cores_count, 8)
        self.assertEquals(os.storage, 587200)
