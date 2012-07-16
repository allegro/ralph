# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from django.test import TestCase
import mock
import datetime
from lck.lang import Null, nullify
import StringIO

from ralph.discovery.plugins import http
from ralph.discovery.plugins import http_supermicro
from ralph.discovery.plugins import ipmi
from ralph.discovery.plugins import ilo_hp
from ralph.discovery.plugins import hp_oa
from ralph.discovery.plugins import snmp
from ralph.discovery.plugins import ssh_ssg
from ralph.discovery.plugins import ssh_aix

from ralph.discovery.models import DeviceType, Device, IPAddress, DiskShare


class MockSSH(object):
    """Utility for mocking the SSHClient objects."""

    class Error(Exception):
        pass

    def __init__(self, data):
        self.data_iter = iter(data)

    def __call__(self, *args, **kwargs):
        return self

    def exec_command(self, command):
        cmd, data = self.data_iter.next()
        if cmd != command:
            raise self.Error("Expected command %r but got %r" % (cmd, command))
        return None, StringIO.StringIO(data), None

    def ssg_command(self, command):
        stdin, stdout, stderr = self.exec_command(command)
        return stdout.readlines()

    def __getattr__(self, name):
        return mock.Mock()


class ModelsTest(TestCase):
    def test_device_create_empty(self):
        with self.assertRaises(ValueError):
            Device.create(model_name='xxx', model_type=DeviceType.unknown)

    def test_device_create_nomodel(self):
        with self.assertRaises(ValueError):
            Device.create(sn='xxx')

    def test_device_conflict(self):
        Device.create([('1', 'DEADBEEFCAFE', 0)],
                      model_name='xxx', model_type=DeviceType.rack_server)
        Device.create([('1', 'CAFEDEADBEEF', 0)],
                      model_name='xxx', model_type=DeviceType.rack_server)
        with self.assertRaises(ValueError):
            Device.create([('1', 'DEADBEEFCAFE', 0), ('2', 'CAFEDEADBEEF', 0)],
                          model_name='yyy', model_type=DeviceType.switch)

    def test_device_create_blacklist(self):
        ethernets = [
            ('1', 'DEADBEEFCAFE', 0),
            ('2', 'DEAD2CEFCAFE', 0),
        ]
        dev = Device.create(ethernets, sn='None',
                            model_name='xxx', model_type=DeviceType.unknown)

        self.assertEqual(dev.sn, None)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(macs, ['DEADBEEFCAFE'])


class HttpPluginTest(TestCase):
    def test_guess_family_empty(self):
        family = http.guess_family({}, '')
        self.assertEqual(family, 'Unspecified')

    def test_guess_family_sun(self):
        family = http.guess_family({'Server': 'Sun-ILOM-Web-Server'}, '')
        self.assertEqual(family, 'Sun')

    def test_guess_family_f5(self):
        family = http.guess_family({'Server': 'Apache'}, '<title>BIG-IP</title>')
        self.assertEqual(family, 'F5')


class IpmiPluginTest(TestCase):
    DATA_SUN = {
            ('fru', 'print'): """\
FRU Device Description : Builtin FRU Device (ID 0)
 Product Manufacturer  : Oracle Corporation
 Product Name          : ILOM INTEGRATED SP

FRU Device Description : /SYS (ID 3)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASSY,MOTHERBOARD,X4170/X4270/X4275  
 Board Serial          : 9328MSL-09304H08BT
 Board Part Number     : 501-7917-11
 Board Extra           : 54
 Board Extra           : X4170/4270/4275
 Product Manufacturer  : ORACLE CORPORATION  
 Product Name          : SUN FIRE X4270 SERVER   
 Product Part Number   : 4457207-6
 Product Serial        : 0936XF707F
 Product Extra         : 080020FFFFFFFFFFFFFF00144FE79268

FRU Device Description : MB (ID 4)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASSY,MOTHERBOARD,X4170/X4270/X4275  
 Board Serial          : 9328MSL-09304H08BT
 Board Part Number     : 501-7917-11
 Board Extra           : 54
 Board Extra           : X4170/4270/4275
 Product Manufacturer  : ORACLE CORPORATION  
 Product Name          : SUN FIRE X4270 SERVER   
 Product Part Number   : 4457207-6
 Product Serial        : 9936XF707F
 Product Extra         : 080020FFFFFFFFFFFFFF00144FE79268

FRU Device Description : MB/BIOS (ID 5)
 Product Manufacturer  : AMERICAN MEGATRENDS 
 Product Name          : SYSTEM BIOS 
 Product Part Number   : AMIBIOS8
 Product Version       : 07060304

FRU Device Description : CPLD (ID 8)
 Product Name          : CPLD
 Product Version       : FW:1.6

FRU Device Description : MB/NET0 (ID 43)
 Product Manufacturer  : INTEL   
 Product Name          : GIGABIT ETHERNET CONTROLLERS
 Product Part Number   : 82575EB
 Product Serial        : 00:14:4F:E7:92:69
 Product Extra         : 01
 Product Extra         : 00:14:4F:E7:92:64

FRU Device Description : MB/NET1 (ID 44)
 Product Manufacturer  : INTEL   
 Product Name          : GIGABIT ETHERNET CONTROLLERS
 Product Part Number   : 82575EB
 Product Serial        : 00:14:4F:E7:92:69
 Product Extra         : 01
 Product Extra         : 00:14:4F:E7:92:65

FRU Device Description : MB/NET2 (ID 45)
 Product Manufacturer  : INTEL   
 Product Name          : GIGABIT ETHERNET CONTROLLERS
 Product Part Number   : 82575EB
 Product Serial        : 00:14:4F:E7:92:69
 Product Extra         : 01
 Product Extra         : 00:14:4F:E7:92:66

FRU Device Description : MB/NET3 (ID 46)
 Product Manufacturer  : INTEL   
 Product Name          : GIGABIT ETHERNET CONTROLLERS
 Product Part Number   : 82575EB
 Product Serial        : 00:14:4F:E7:92:69
 Product Extra         : 01
 Product Extra         : 00:14:4F:E7:92:67

FRU Device Description : /UUID (ID 6)
 Product Extra         : 080020FFFFFFFFFFFFFF00144FE79268

FRU Device Description : SP/NET0 (ID 1)
 Product Manufacturer  : ASPEED
 Product Name          : ETHERNET CONTROLLER
 Product Part Number   : AST2100
 Product Serial        : 00:14:4f:e7:92:69

FRU Device Description : SP/NET1 (ID 2)
 Product Manufacturer  : ASPEED
 Product Name          : ETHERNET CONTROLLER
 Product Part Number   : AST2100
 Product Serial        : 00:14:4f:e7:92:69

FRU Device Description : MB/P0 (ID 16)
 Product Manufacturer  : INTEL   
 Product Name          : INTEL(R) XEON(R) CPU           L5520  @ 2.27GHZ 
 Product Part Number   : 060A
 Product Version       : 05

FRU Device Description : MB/P1 (ID 17)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P0/D0 (ID 24)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P0/D1 (ID 25)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 42221369

FRU Device Description : MB/P0/D2 (ID 26)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 9222085A

FRU Device Description : MB/P0/D3 (ID 27)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P0/D4 (ID 28)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 922214AF

FRU Device Description : MB/P0/D5 (ID 29)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 922212FE

FRU Device Description : MB/P0/D6 (ID 30)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P0/D7 (ID 31)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 92221301

FRU Device Description : MB/P0/D8 (ID 32)
 Product Manufacturer  : SAMSUNG 
 Product Name          : 4GB DDR3 SDRAM 666  
 Product Part Number   : M393B5170EH1-CH9  
 Product Version       : 00
 Product Serial        : 9221B058

FRU Device Description : MB/P1/D0 (ID 33)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D1 (ID 34)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D2 (ID 35)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D3 (ID 36)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D4 (ID 37)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D5 (ID 38)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D6 (ID 39)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D7 (ID 40)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/P1/D8 (ID 41)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : PCIE1/F20CARD (ID 225)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : PCIE2/F20CARD (ID 226)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : PCIE4/F20CARD (ID 228)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : PCIE5/F20CARD (ID 229)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : MB/R1 (ID 220)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASSY,ACTIVE_RISER,X4270/X4275   
 Board Serial          : 9328MSL-09275K04PC
 Board Part Number     : 511-1139-02
 Board Extra           : 50
 Board Extra           : ACTIVE_RISER

FRU Device Description : MB/R2 (ID 221)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASSY,ACTIVE_RISER,X4270/X4275   
 Board Serial          : 9328MSL-09275K04PD
 Board Part Number     : 511-1139-02
 Board Extra           : 50
 Board Extra           : ACTIVE_RISER

FRU Device Description : PS0 (ID 63)
 Board Mfg Date        : Wed Jun 24 19:44:00 2009
 Board Mfg             : POWER ONE
 Board Product         : A217
 Board Serial          : 9908BAO-0926A30L9J
 Board Part Number     : 300-1897-04

FRU Device Description : PS1 (ID 64)
 Board Mfg Date        : Tue Jun  9 20:01:00 2009
 Board Mfg             : POWER ONE
 Board Product         : A217
 Board Serial          : 9908BAO-0924A30JG9
 Board Part Number     : 300-1897-04

FRU Device Description : DBP (ID 210)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : BD,SATA,16DSK,BKPL,2U   
 Board Serial          : A3921H
 Board Part Number     : 511-1257-02
 Board Extra           : 50
 Board Extra           : SASBP

FRU Device Description : PDB (ID 211)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : PDB,H+V,BUS_BAR,2U  
 Board Serial          : 9226LHF-0930B500MC
 Board Part Number     : 541-2073-09
 Board Extra           : 50
 Board Extra           : PDB
 Product Part Number   : 4457207-6
 Product Serial        : 9936XF707F

FRU Device Description : PADCRD (ID 222)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : BD,SATA,2U,PADDLE_CARD  
 Board Serial          : 9226LHF-09300001MG
 Board Part Number     : 541-3513-02
 Board Extra           : 50
 Board Extra           : 2U Paddle

FRU Device Description : FB0 (ID 212)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASY,FAN,BOARD,H2M2G2
 Board Serial          : 9226LHF-0930B301H3
 Board Part Number     : 541-2211-04
 Board Extra           : 50
 Board Extra           : FANBD

FRU Device Description : FB1 (ID 213)
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Product         : ASY,FAN,BOARD,H2M2G2
 Board Serial          : 9226LHF-0930B301H5
 Board Part Number     : 541-2211-04
 Board Extra           : 50
 Board Extra           : FANBD

FRU Device Description : DBP/HDD0 (ID 47)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD1 (ID 48)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD2 (ID 49)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD3 (ID 50)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD4 (ID 51)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD5 (ID 52)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD6 (ID 53)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD7 (ID 54)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD8 (ID 55)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD9 (ID 56)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD10 (ID 57)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD11 (ID 58)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD12 (ID 59)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD13 (ID 60)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD14 (ID 61)
 Device not present (Requested sensor, data, or record not found)

FRU Device Description : DBP/HDD15 (ID 62)
 Device not present (Requested sensor, data, or record not found)
""",
    }
    DATA_KRENN = {
            ('fru', 'print'): """\
FRU Device Description : Builtin FRU Device (ID 0)
 Chassis Type                    : Unknown
 Chassis Part Number     : SC113TQ-R650CB
 Board Mfg Date        : Mon Jan  1 00:00:00 1996
 Board Mfg             : Super Micro
 Board Product         : X8DT3-LN4F
 Board Serial          :           
 Board Part Number     : Winbond Hermon
 Product Manufacturer  : Thomas-Krenn.AG
 Product Name          : 1HE Supermicro SC113TQ-R650CB
 Product Part Number   : SC113TQ
 Product Serial        : 9000078907
""",
    }

    def test_fru_empty(self):
        data = {
            ('fru', 'print'): '',
        }
        session = ipmi.IPMI('localhost')
        session.tool = lambda c, s: data.get((c, s))
        fru = session.get_fru()
        self.assertEqual(fru, {})

    def test_fru_thomas_krenn(self):
        session = ipmi.IPMI('localhost')
        session.tool = lambda c, s: self.DATA_KRENN.get((c, s))
        fru = session.get_fru()
        self.assertEqual(fru, {
            'Builtin FRU Device': {
                'Board Serial': '',
                'Product Part Number': 'SC113TQ',
                'Product Serial': '9000078907',
                'Board Part Number': 'Winbond Hermon',
                'Product Manufacturer': 'Thomas-Krenn.AG',
                'Chassis Type': 'Unknown',
                'Chassis Part Number': 'SC113TQ-R650CB',
                'Product Name': '1HE Supermicro SC113TQ-R650CB',
                'Board Product': 'X8DT3-LN4F',
                None: 'FRU Device Description',
                'Board Mfg': 'Super Micro',
                'Board Mfg Date': 'Mon Jan  1 00:00:00 1996'
            }
        })

    def test_fru_sun_fire(self):
        session = ipmi.IPMI('localhost')
        session.tool = lambda c, s: self.DATA_SUN.get((c, s))
        fru = session.get_fru()
        self.assertEqual(fru, {
            '/SYS': {
                None: 'FRU Device Description',
                'Board Extra': 'X4170/4270/4275',
                'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                'Board Part Number': '501-7917-11',
                'Board Product': 'ASSY,MOTHERBOARD,X4170/X4270/X4275',
                'Board Serial': '9328MSL-09304H08BT',
                'Product Extra': '080020FFFFFFFFFFFFFF00144FE79268',
                'Product Manufacturer': 'ORACLE CORPORATION',
                'Product Name': 'SUN FIRE X4270 SERVER',
                'Product Part Number': '4457207-6',
                'Product Serial': '0936XF707F'
            },
            '/UUID': {
                None: 'FRU Device Description',
                'Product Extra': '080020FFFFFFFFFFFFFF00144FE79268'
            },
            'Builtin FRU Device': {
                None: 'FRU Device Description',
                'Product Manufacturer': 'Oracle Corporation',
                'Product Name': 'ILOM INTEGRATED SP'
            },
            'CPLD': {
                None: 'FRU Device Description',
                'Product Name': 'CPLD',
                'Product Version': 'FW:1.6'
            },
            'DBP': {
                None: 'FRU Device Description',
                'Board Extra': 'SASBP',
                'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                'Board Part Number': '511-1257-02',
                'Board Product': 'BD,SATA,16DSK,BKPL,2U',
                'Board Serial': 'A3921H'
            },
            'DBP/HDD0': {
                None: 'FRU Device Description',
                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'
            },
            'DBP/HDD1': {
                None: 'FRU Device Description',
                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'
            },
            'DBP/HDD10': {
                None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD11': {None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD12': {None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD13': {None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD14': {None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD15': {None: 'FRU Device Description',
                            'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD2': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD3': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD4': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD5': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD6': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD7': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD8': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'DBP/HDD9': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'FB0': {None: 'FRU Device Description',
                      'Board Extra': 'FANBD',
                      'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                      'Board Part Number': '541-2211-04',
                      'Board Product': 'ASY,FAN,BOARD,H2M2G2',
                      'Board Serial': '9226LHF-0930B301H3'},
             'FB1': {None: 'FRU Device Description',
                      'Board Extra': 'FANBD',
                      'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                      'Board Part Number': '541-2211-04',
                      'Board Product': 'ASY,FAN,BOARD,H2M2G2',
                      'Board Serial': '9226LHF-0930B301H5'},
             'MB': {None: 'FRU Device Description',
                     'Board Extra': 'X4170/4270/4275',
                     'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                     'Board Part Number': '501-7917-11',
                     'Board Product': 'ASSY,MOTHERBOARD,X4170/X4270/X4275',
                     'Board Serial': '9328MSL-09304H08BT',
                     'Product Extra': '080020FFFFFFFFFFFFFF00144FE79268',
                     'Product Manufacturer': 'ORACLE CORPORATION',
                     'Product Name': 'SUN FIRE X4270 SERVER',
                     'Product Part Number': '4457207-6',
                     'Product Serial': '9936XF707F'},
             'MB/BIOS': {None: 'FRU Device Description',
                          'Product Manufacturer': 'AMERICAN MEGATRENDS',
                          'Product Name': 'SYSTEM BIOS',
                          'Product Part Number': 'AMIBIOS8',
                          'Product Version': '07060304'},
             'MB/NET0': {None: 'FRU Device Description',
                          'Product Extra': '00:14:4F:E7:92:64',
                          'Product Manufacturer': 'INTEL',
                          'Product Name': 'GIGABIT ETHERNET CONTROLLERS',
                          'Product Part Number': '82575EB',
                          'Product Serial': '00:14:4F:E7:92:69'},
             'MB/NET1': {None: 'FRU Device Description',
                          'Product Extra': '00:14:4F:E7:92:65',
                          'Product Manufacturer': 'INTEL',
                          'Product Name': 'GIGABIT ETHERNET CONTROLLERS',
                          'Product Part Number': '82575EB',
                          'Product Serial': '00:14:4F:E7:92:69'},
             'MB/NET2': {None: 'FRU Device Description',
                          'Product Extra': '00:14:4F:E7:92:66',
                          'Product Manufacturer': 'INTEL',
                          'Product Name': 'GIGABIT ETHERNET CONTROLLERS',
                          'Product Part Number': '82575EB',
                          'Product Serial': '00:14:4F:E7:92:69'},
             'MB/NET3': {None: 'FRU Device Description',
                          'Product Extra': '00:14:4F:E7:92:67',
                          'Product Manufacturer': 'INTEL',
                          'Product Name': 'GIGABIT ETHERNET CONTROLLERS',
                          'Product Part Number': '82575EB',
                          'Product Serial': '00:14:4F:E7:92:69'},
             'MB/P0': {None: 'FRU Device Description',
                        'Product Manufacturer': 'INTEL',
                        'Product Name': 'INTEL(R) XEON(R) CPU           L5520  @ 2.27GHZ',
                        'Product Part Number': '060A',
                        'Product Version': '05'},
             'MB/P0/D0': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P0/D1': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '42221369',
                           'Product Version': '00'},
             'MB/P0/D2': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '9222085A',
                           'Product Version': '00'},
             'MB/P0/D3': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P0/D4': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '922214AF',
                           'Product Version': '00'},
             'MB/P0/D5': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '922212FE',
                           'Product Version': '00'},
             'MB/P0/D6': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P0/D7': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '92221301',
                           'Product Version': '00'},
             'MB/P0/D8': {None: 'FRU Device Description',
                           'Product Manufacturer': 'SAMSUNG',
                           'Product Name': '4GB DDR3 SDRAM 666',
                           'Product Part Number': 'M393B5170EH1-CH9',
                           'Product Serial': '9221B058',
                           'Product Version': '00'},
             'MB/P1': {None: 'FRU Device Description',
                        'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D0': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D1': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D2': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D3': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D4': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D5': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D6': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D7': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/P1/D8': {None: 'FRU Device Description',
                           'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'MB/R1': {None: 'FRU Device Description',
                        'Board Extra': 'ACTIVE_RISER',
                        'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                        'Board Part Number': '511-1139-02',
                        'Board Product': 'ASSY,ACTIVE_RISER,X4270/X4275',
                        'Board Serial': '9328MSL-09275K04PC'},
             'MB/R2': {None: 'FRU Device Description',
                        'Board Extra': 'ACTIVE_RISER',
                        'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                        'Board Part Number': '511-1139-02',
                        'Board Product': 'ASSY,ACTIVE_RISER,X4270/X4275',
                        'Board Serial': '9328MSL-09275K04PD'},
             'PADCRD': {None: 'FRU Device Description',
                         'Board Extra': '2U Paddle',
                         'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                         'Board Part Number': '541-3513-02',
                         'Board Product': 'BD,SATA,2U,PADDLE_CARD',
                         'Board Serial': '9226LHF-09300001MG'},
             'PCIE1/F20CARD': {None: 'FRU Device Description',
                                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'PCIE2/F20CARD': {None: 'FRU Device Description',
                                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'PCIE4/F20CARD': {None: 'FRU Device Description',
                                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'PCIE5/F20CARD': {None: 'FRU Device Description',
                                'Device not present (Requested sensor, data, or record not found)': 'Device not present (Requested sensor, data, or record not found)'},
             'PDB': {None: 'FRU Device Description',
                      'Board Extra': 'PDB',
                      'Board Mfg Date': 'Mon Jan  1 00:00:00 1996',
                      'Board Part Number': '541-2073-09',
                      'Board Product': 'PDB,H+V,BUS_BAR,2U',
                      'Board Serial': '9226LHF-0930B500MC',
                      'Product Part Number': '4457207-6',
                      'Product Serial': '9936XF707F'},
             'PS0': {None: 'FRU Device Description',
                      'Board Mfg': 'POWER ONE',
                      'Board Mfg Date': 'Wed Jun 24 19:44:00 2009',
                      'Board Part Number': '300-1897-04',
                      'Board Product': 'A217',
                      'Board Serial': '9908BAO-0926A30L9J'},
             'PS1': {None: 'FRU Device Description',
                      'Board Mfg': 'POWER ONE',
                      'Board Mfg Date': 'Tue Jun  9 20:01:00 2009',
                      'Board Part Number': '300-1897-04',
                      'Board Product': 'A217',
                      'Board Serial': '9908BAO-0924A30JG9'},
             'SP/NET0': {None: 'FRU Device Description',
                          'Product Manufacturer': 'ASPEED',
                          'Product Name': 'ETHERNET CONTROLLER',
                          'Product Part Number': 'AST2100',
                          'Product Serial': '00:14:4f:e7:92:69'},
             'SP/NET1': {None: 'FRU Device Description',
                          'Product Manufacturer': 'ASPEED',
                          'Product Name': 'ETHERNET CONTROLLER',
                          'Product Part Number': 'AST2100',
                          'Product Serial': '00:14:4f:e7:92:69'}
        })

    def test_components(self):
        session = ipmi.IPMI('localhost')
        session.tool = lambda c, s: self.DATA_SUN.get((c, s))
        fru = session.get_fru()
        dev = Device.create(sn='00010101', model_name='Sun Fire',
                            model_type=DeviceType.rack_server, priority=0)
        ipmi._add_ipmi_components(dev, fru)

        cpus = dev.processor_set.all()
        self.assertEquals(len(cpus), 1)
        self.assertEquals(cpus[0].index, 1)
        self.assertEquals(cpus[0].model.name,
                        'CPU Intel(R) Xeon(R) Cpu L5520 @ 2.27Ghz 2270MHz 0')
        self.assertEquals(cpus[0].label,
                        'Intel(R) Xeon(R) Cpu L5520 @ 2.27Ghz')

        mem = dev.memory_set.all()
        sizes = [m.size or m.model.size for m in mem]
        self.assertEquals(sizes, [4096] * 6)
        labels = [m.label for m in mem]
        self.assertEquals(labels, ['4GB DDR3 SDRAM 666'] * 6)


class IloHpPluginTest(TestCase):
    RAW = """<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
<INFORM>Scripting utility should be updated to the latest version.</INFORM>
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
<GET_NETWORK_SETTINGS>
    <ENABLE_NIC VALUE="Y"/>
    <SPEED_AUTOSELECT VALUE="Y"/>
    <NIC_SPEED VALUE="10"/>
    <FULL_DUPLEX VALUE="N"/>
    <DHCP_ENABLE VALUE="Y"/>
    <DHCP_GATEWAY VALUE="Y"/>
    <DHCP_DNS_SERVER VALUE="Y"/>
    <DHCP_WINS_SERVER VALUE="Y"/>
    <DHCP_STATIC_ROUTE VALUE="Y"/>
    <DHCP_DOMAIN_NAME VALUE="Y"/>
    <REG_WINS_SERVER VALUE="Y"/>
    <REG_DDNS_SERVER VALUE="Y"/>
    <PING_GATEWAY VALUE="N"/>
    <MAC_ADDRESS VALUE="00:21:5a:af:a3:d8"/>
    <IP_ADDRESS VALUE="10.235.160.108"/>
    <SUBNET_MASK VALUE="255.255.0.0"/>
    <GATEWAY_IP_ADDRESS VALUE="10.235.0.1"/>
    <DNS_NAME VALUE="ILOGB8911KH35"/>
    <DOMAIN_NAME VALUE="dc2"/>
    <PRIM_DNS_SERVER VALUE="10.238.0.11"/>
    <SEC_DNS_SERVER VALUE="10.238.0.12"/>
    <TER_DNS_SERVER VALUE="0.0.0.0"/>
    <PRIM_WINS_SERVER VALUE="0.0.0.0"/>
    <SEC_WINS_SERVER VALUE="0.0.0.0"/>
    <STATIC_ROUTE_1 DEST="0.0.0.0"
                    GATEWAY="0.0.0.0"/>
    <STATIC_ROUTE_2 DEST="0.0.0.0"
                    GATEWAY="0.0.0.0"/>
    <STATIC_ROUTE_3 DEST="0.0.0.0"
                    GATEWAY="0.0.0.0"/>
</GET_NETWORK_SETTINGS>
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
<GET_FW_VERSION
   FIRMWARE_VERSION = "1.70"
   FIRMWARE_DATE    = "Dec 02 2008"
   MANAGEMENT_PROCESSOR    = "iLO2"
    />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
<GET_HOST_DATA>
 <SMBIOS_RECORD TYPE="0" B64_DATA="ABgAAAECAPADH4DayX0AAAAAAwf/////SFAASTE5ADExLzAyLzIwMDgAAA==">
  <FIELD NAME="Subject" VALUE="BIOS Information"/>
  <FIELD NAME="Family" VALUE="I19"/>
  <FIELD NAME="Date" VALUE="11/02/2008"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="1" B64_DATA="ARsAAQQFAAE0NjU0MDBHQjg5MTFLSDM1BgIDR0I4OTExS0gzNSAgICAgIAA0NjU0MDAtQjIxICAgICAgAFByb0xpYW50AEhQAFByb0xpYW50IEJMMngyMjBjIEc1ACAgICAgICAgICAgICAAAA==">
  <FIELD NAME="Subject" VALUE="System Information"/>
  <FIELD NAME="Product Name" VALUE="ProLiant BL2x220c G5"/>
  <FIELD NAME="Serial Number" VALUE="GB8911KH35      "/>
  <FIELD NAME="cUUID" VALUE="34353634-3030-4247-3839-31314B483335"/>
  <FIELD NAME="UUID" VALUE="465400GB8911KH35"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="3" B64_DATA="AxMAAwEXAAIDAgICAgAAAAABAEhQAENaMzA1MTY2V1MgICAAICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAAAA=="/>
 <SMBIOS_RECORD TYPE="4" B64_DATA="BCgABAEDswJ6BgEA//vrvwCLNQXAEsQJQRQQByAHMAcAAAAEBAQEAFByb2MgMQBJbnRlbAAA">
  <FIELD NAME="Subject" VALUE="Processor Information"/>
  <FIELD NAME="Label" VALUE="Proc 1"/>
  <FIELD NAME="Speed" VALUE="2500 MHz"/>
  <FIELD NAME="Execution Technology" VALUE="4 of 4 cores; 4 threads"/>
  <FIELD NAME="Memory Technology" VALUE="64-bit extensions"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="4" B64_DATA="BCgGBAEDswJ6BgEA//vrvwCLNQXAEsQJRBQWByYHNgcAAAAEBAQEAFByb2MgMgBJbnRlbAAA">
  <FIELD NAME="Subject" VALUE="Processor Information"/>
  <FIELD NAME="Label" VALUE="Proc 2"/>
  <FIELD NAME="Speed" VALUE="2500 MHz"/>
  <FIELD NAME="Execution Technology" VALUE="4 of 4 cores; 4 threads"/>
  <FIELD NAME="Memory Technology" VALUE="64-bit extensions"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxMQBwGAAYAAgAAIAAgAAAUEB1Byb2Nlc3NvciAxIEludGVybmFsIEwxIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxMWBwGAAYAAgAAIAAgAAAUEB1Byb2Nlc3NvciAyIEludGVybmFsIEwxIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxMgBwGBAQCBwIAIAAgAAAUCB1Byb2Nlc3NvciAxIEludGVybmFsIEwyIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxMmBwGBAQCBwIAIAAgAAAUCB1Byb2Nlc3NvciAyIEludGVybmFsIEwyIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxMwBwGCAYCAAIAIAAgAAAUCAVByb2Nlc3NvciAxIEludGVybmFsIEwzIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="7" B64_DATA="BxM2BwGCAYCAAIAIAAgAAAUCAVByb2Nlc3NvciAyIEludGVybmFsIEwzIENhY2hlAAA="/>
 <SMBIOS_RECORD TYPE="9" B64_DATA="CQ0BCQGlCwMEAQAEAVBDSS1FIFNsb3QgMQAA">
  <FIELD NAME="Subject" VALUE="System Slots"/>
  <FIELD NAME="Label" VALUE="PCI-E Slot 1"/>
  <FIELD NAME="Type" VALUE="PCI Express"/>
  <FIELD NAME="Width" VALUE="8x"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="11" B64_DATA="CwUACwFQcm9kdWN0IElEOiA0NjU0MDAtQjIxICAgICAgAAA="/>
 <SMBIOS_RECORD TYPE="32" B64_DATA="IAsAIAAAAAAAAAAAAA=="/>
 <SMBIOS_RECORD TYPE="38" B64_DATA="JhIAJgEgIP+jDAAAAAAAAAAAAAA="/>
 <SMBIOS_RECORD TYPE="193" B64_DATA="wQcAwQABAk4vQQAwMi8wMS8yMDA4AAA=">
  <FIELD NAME="Subject" VALUE="Other ROM Info"/>
  <FIELD NAME="Redundant ROM Present" VALUE="No"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="194" B64_DATA="wgUAwgEAAA=="/>
 <SMBIOS_RECORD TYPE="195" B64_DATA="wwUAwwEkMEUxMTA3OEEAAA=="/>
 <SMBIOS_RECORD TYPE="196" B64_DATA="xAUAxAAAAA=="/>
 <SMBIOS_RECORD TYPE="197" B64_DATA="xQoAxQAEAAH/AQAA"/>
 <SMBIOS_RECORD TYPE="223" B64_DATA="3wcA32ZGcAAA"/>
 <SMBIOS_RECORD TYPE="197" B64_DATA="xQoGxQYEBwD/AgAA"/>
 <SMBIOS_RECORD TYPE="211" B64_DATA="0wcA0wAESAAA"/>
 <SMBIOS_RECORD TYPE="211" B64_DATA="0wcG0wYESAAA"/>
 <SMBIOS_RECORD TYPE="198" B64_DATA="xgsAxgEAAAE8AAEAAA=="/>
 <SMBIOS_RECORD TYPE="199" B64_DATA="x2QAxwcKAAAIIAkEegYBAAwGAAAIIBkBdgYBAAwGAAAIIBkBdgYBAAQEAAAHIAgGdAYBAAQEAAAHIAgGdAYBAAYBAAAHICkDcQYBAAYBAAAHICkDcQYBALQAAAAHIBQD+wYAAAAA"/>
 <SMBIOS_RECORD TYPE="205" B64_DATA="zRYAzQEBRkFUeAAA4v8AAAAAAAANAAAA"/>
 <SMBIOS_RECORD TYPE="209" B64_DATA="0RQA0SADACFar8cSIQMAIVqvxxMAAA==">
  <FIELD NAME="Subject" VALUE="Embedded NIC MAC Assignment"/>
  <FIELD NAME="Port" VALUE="1"/>
  <FIELD NAME="MAC" VALUE="00-21-5A-AF-C7-12"/>
  <FIELD NAME="Port" VALUE="2"/>
  <FIELD NAME="MAC" VALUE="00-21-5A-AF-C7-13"/>
  <FIELD NAME="Port" VALUE="iLO"/>
  <FIELD NAME="MAC" VALUE="00-21-5A-AF-A3-D8"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="210" B64_DATA="0gwA0roAAAAAAAAAAAA="/>
 <SMBIOS_RECORD TYPE="212" B64_DATA="1BgA1CRDUlUA4Pj/AAAAAABAAAAAAAAAAAA="/>
 <SMBIOS_RECORD TYPE="213" B64_DATA="1RwA1QAANgAAAL8fAABGAAAAAAAAAAAAAAAAAAAA"/>
 <SMBIOS_RECORD TYPE="214" B64_DATA="1iwA1jExAAIOIAAAEyAAAABgAAAAIAAAAiAAAAQgAAAGIAAADCAAAAggAAAAAA=="/>
 <SMBIOS_RECORD TYPE="215" B64_DATA="1wYA1wAFAAA="/>
 <SMBIOS_RECORD TYPE="219" B64_DATA="2wgA2/8IAAAAAA=="/>
 <SMBIOS_RECORD TYPE="220" B64_DATA="3C0B3AgAAMUA/wEAxQH/AgDFAv8DAMUD/wQGxQL/BQbFA/8GBsUA/wcGxQH/AAA="/>
 <SMBIOS_RECORD TYPE="222" B64_DATA="3kYA3gEI8AAAAPIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"/>
 <SMBIOS_RECORD TYPE="226" B64_DATA="4hUA4jQ2NTQwMEdCODkxMUtIMzUBR0I4OTExS0gzNSAgICAgIAAA">
  <FIELD NAME="Subject" VALUE="HPQ Physical Attributes"/>
  <FIELD NAME="Serial Number" VALUE="GB8911KH35      "/>
  <FIELD NAME="cUUID" VALUE="34353634-3030-4247-3839-31314B483335"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="17" B64_DATA="ERcAEQAQ/v9IAEAAABAJAAEAE4AAmwJESU1NIDFBAAA=">
  <FIELD NAME="Subject" VALUE="Memory Device"/>
  <FIELD NAME="Label" VALUE="DIMM 1A"/>
  <FIELD NAME="Size" VALUE="4096 MB"/>
  <FIELD NAME="Speed" VALUE="667 MHz"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="17" B64_DATA="ERcBEQAQ/v9IAEAAABAJAAEAE4AAmwJESU1NIDJCAAA=">
  <FIELD NAME="Subject" VALUE="Memory Device"/>
  <FIELD NAME="Label" VALUE="DIMM 2B"/>
  <FIELD NAME="Size" VALUE="4096 MB"/>
  <FIELD NAME="Speed" VALUE="667 MHz"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="17" B64_DATA="ERcCEQAQ/v9IAEAAABAJAAEAE4AAmwJESU1NIDNDAAA=">
  <FIELD NAME="Subject" VALUE="Memory Device"/>
  <FIELD NAME="Label" VALUE="DIMM 3C"/>
  <FIELD NAME="Size" VALUE="4096 MB"/>
  <FIELD NAME="Speed" VALUE="667 MHz"/>
 </SMBIOS_RECORD>
 <SMBIOS_RECORD TYPE="17" B64_DATA="ERcDEQAQ/v9IAEAAABAJAAEAE4AAmwJESU1NIDREAAA=">
  <FIELD NAME="Subject" VALUE="Memory Device"/>
  <FIELD NAME="Label" VALUE="DIMM 4D"/>
  <FIELD NAME="Size" VALUE="4096 MB"/>
  <FIELD NAME="Speed" VALUE="667 MHz"/>
 </SMBIOS_RECORD>
</GET_HOST_DATA>
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
<?xml version="1.0"?>
<RIBCL VERSION="2.22"/>
<RESPONSE
    STATUS="0x0000"
    MESSAGE='No error'
     />
</RIBCL>
"""
    def test_device(self):
        ilo = ilo_hp.hp_ilo.IloHost('127.0.0.1', '', '')
        ilo.update(raw=self.RAW)
        dev = ilo_hp.make_device(ilo, '127.0.0.1')
        self.assertEqual(dev.name, '')
        self.assertEqual(dev.sn, 'GB8911KH35')
        self.assertEqual(dev.model.type, DeviceType.blade_server.id)
        self.assertEqual(dev.model.name, 'HP ProLiant BL2x220c G5')
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(macs, ['00215AAFA3D8', '00215AAFC712', '00215AAFC713'])

    def test_components(self):
        ilo = ilo_hp.hp_ilo.IloHost('127.0.0.1', '', '')
        ilo.update(raw=self.RAW)
        dev = ilo_hp.make_device(ilo, '127.0.0.1')
        ilo_hp.make_components(ilo, dev)
        sizes = [m.size or m.model.size for m in dev.memory_set.all()]
        self.assertEqual(sizes, [4096] * 4)
        labels = [m.label for m in dev.memory_set.all()]
        self.assertEqual(labels, ['DIMM 1A', 'DIMM 2B', 'DIMM 3C', 'DIMM 4D'])
        cpus = [p.label for p in dev.processor_set.all()]
        self.assertEqual(cpus, ['Proc 1', 'Proc 2'])
        models = [p.model.name for p in dev.processor_set.all()]
        self.assertEqual(models, ['CPU  2500MHz, 4-core', 'CPU  2500MHz, 4-core'])


class HttpSupermicroPluginTest(TestCase):
    def test_macs(self):
        opener = mock.Mock()
        request_session = mock.Mock()
        request_session.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_WEB_SESSION = 

 { 

 WEBVAR_STRUCTNAME_WEB_SESSION : 

 [ 

 { 'SESSION_COOKIE' : 'xmBo2KB9rZCknX73xSfoy0DiMxXua3Fk001' },  {} ],  

 HAPI_STATUS:0 }; 

//Dynamic data end


"""
        request_macs = mock.Mock()
        request_macs.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_GETMBMAC = 

 { 

 WEBVAR_STRUCTNAME_GETMBMAC : 

 [ 

 { 'MAC1' : '00:25:90:1E:BF:22','MAC2' : '00:25:90:1E:BF:23' },  {} ],  

 HAPI_STATUS:0 }; 

//Dynamic data end



"""
        request_mgmt = mock.Mock()
        request_mgmt.raw = """\
//Dynamic Data Begin

 WEBVAR_JSONVAR_HL_GETLANCONFIG = 

 { 

 WEBVAR_STRUCTNAME_HL_GETLANCONFIG : 

 [ 

 { 'IPAddrSource' : 1,'MAC' : '00:25:90:2C:E5:CC','IP' : '10.235.29.201','Mask' : '255.255.0.0','Gateway' : '10.235.0.1','PrimaryDNS' : '10.10.10.1','SecondaryDNS' : '','VLanEnable' : 0,'VLANID' : 0 },  {} ],  

 HAPI_STATUS:0 }; 

//Dynamic data end


"""
        def open_side(request, timeout):
            response = mock.Mock()
            response.readlines.return_value = request.raw.splitlines()
            return response
        opener.open.side_effect = open_side
        def request_side(url, *args, **kwargs):
            if url.endswith('WEBSES/create.asp'):
                return request_session
            elif url.endswith('rpc/getmbmac.asp'):
                return request_macs
            elif url.endswith('rpc/getnwconfig.asp'):
                return request_mgmt
        with mock.patch('ralph.discovery.plugins.http_supermicro.urllib2') as urllib2:
            urllib2.build_opener.return_value = opener
            urllib2.Request.side_effect = request_side
            macs = http_supermicro._get_macs('127.0.0.1')
        self.assertEquals(macs, {
            'IPMI MC': '00:25:90:2C:E5:CC',
            'MAC2': '00:25:90:1E:BF:23',
            'MAC1': '00:25:90:1E:BF:22'
        })

class HpOaPluginTest(TestCase):
    DATA = {'INFRA2': {'ADDR': 'A9FE0111',
            'ASSET': Null,
            'BLADES': {'BAYS': {'BAY': [{'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 0,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 56,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 112,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 168,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 224,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 280,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 336,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 392,
                                         'mmYOffset': 7},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 0,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 56,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 112,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 168,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 224,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 280,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 336,
                                         'mmYOffset': 188},
                                        {'SIDE': 'FRONT',
                                         'mmDepth': 480,
                                         'mmHeight': 181,
                                         'mmWidth': 56,
                                         'mmXOffset': 392,
                                         'mmYOffset': 188}]},
                       'BLADE': [{'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 1},
                                  'BSN': 'GB8849BBRD      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.151',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:64:9a'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:64:9b'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 1},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 1}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 1},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 1},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 1},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 1}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:22:64:9C:6F:F6',
                                                                             'iSCSI': '00:22:64:9C:6F:F7'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:22:64:9C:7F:42',
                                                                             'iSCSI': '00:22:64:9C:7F:43'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 1},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 1}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 186},
                                  'SPN': 'ProLiant BL460c G1',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 20,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 38,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 43,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '447707GB8849BBRD',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '37373434-3730-4247-3838-343942425244'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 2},
                                  'BSN': 'CZJ70601RN      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.152',
                                  'PORTMAP': {'MEZZ': [{'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 2},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 2}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'DEVICE': {'NAME': 'QLogic QMH2462 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'UNKNOWN',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:b5:a0'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'UNKNOWN',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:b5:a2'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 2},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 2},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 2},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 2}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:1A:4B:D0:DC:14',
                                                                             'iSCSI': '00:1A:4B:D0:DC:15'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:1A:4B:D0:CC:0E',
                                                                             'iSCSI': '00:1A:4B:D0:CC:0F'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 2},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 2}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 309},
                                  'SPN': 'ProLiant BL460c G1',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 20,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 38,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 43,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '416656CZJ70601RN',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '36363134-3635-5A43-4A37-30363031524E'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 3},
                                  'BSN': 'GB8926V80C      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.153',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'QLogic QMH2462 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:43:80:03:b9:e7:c0'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:43:80:03:b9:e7:c2'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 3},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 3}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 3},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 3},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 3},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 3}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:14:68',
                                                                             'iSCSI': '00:25:B3:A3:14:69'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:14:6C',
                                                                             'iSCSI': '00:25:B3:A3:14:6D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 3},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 3}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 232},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 20,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V80C',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383043'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 4},
                                  'BSN': 'GB8908J72D      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.154',
                                  'PORTMAP': {'MEZZ': [{'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 4},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 4}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 4},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 4},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 4},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 4}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:23:7D:A9:2A:76',
                                                                             'iSCSI': '00:23:7D:A9:2A:77'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:23:7D:A9:2A:70',
                                                                             'iSCSI': '00:23:7D:A9:2A:71'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 4},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 4}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 227},
                                  'SPN': 'ProLiant BL460c G1',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 20,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 38,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 43,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '447707GB8908J72D',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '37373434-3730-4247-3839-30384A373244'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 5},
                                  'BSN': 'CZJ70601PU      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.155',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'QLogic QMH2462 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:b2:a8'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:b2:aa'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 5},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 5}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 5},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 5},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 5},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 5}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:1A:4B:D0:B5:64',
                                                                             'iSCSI': '00:1A:4B:D0:B5:65'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:1A:4B:D0:B5:70',
                                                                             'iSCSI': '00:1A:4B:D0:B5:71'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 5},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 5}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 304},
                                  'SPN': 'ProLiant BL460c G1',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 19,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 38,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 43,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '416656CZJ70601PU',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '36363134-3635-5A43-4A37-303630315055'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 6},
                                  'BSN': 'GB8908J72R      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.156',
                                  'PORTMAP': {'MEZZ': [{'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 6},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 6}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 6},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 6},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 6},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 6}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:23:7D:A9:2B:B0',
                                                                             'iSCSI': '00:23:7D:A9:2B:B1'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:23:7D:A9:2B:B2',
                                                                             'iSCSI': '00:23:7D:A9:2B:B3'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 6},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 6}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 223},
                                  'SPN': 'ProLiant BL460c G1',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 20,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 38,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 43,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '447707GB8908J72R',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '37373434-3730-4247-3839-30384A373252'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 7},
                                  'BSN': 'GB8926V807      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.157',
                                  'PORTMAP': {'MEZZ': [{'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 7},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 7}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 7},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 7},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 7},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 7}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AE:C0:98',
                                                                             'iSCSI': '00:24:81:AE:C0:99'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AE:C0:9C',
                                                                             'iSCSI': '00:24:81:AE:C0:9D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 7},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 7}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 229},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 21,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V807',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383037'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 8},
                                  'BSN': 'GB8926V7WH      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.158',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:fc:2c'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:fc:2d'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 8},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 8}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 8},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 8},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 8},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 8}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:6D:38',
                                                                             'iSCSI': '00:25:B3:A3:6D:39'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:6D:3C',
                                                                             'iSCSI': '00:25:B3:A3:6D:3D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 8},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 8}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 227},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 22,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V7WH',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656375748'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 9},
                                  'BSN': 'GB8926V82E      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.159',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b9:82'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b9:83'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 9},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 9}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 9},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 9},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 9},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 9}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:A2:88',
                                                                             'iSCSI': '00:25:B3:A3:A2:89'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:A2:8C',
                                                                             'iSCSI': '00:25:B3:A3:A2:8D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 9},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 9}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 237},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 26,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V82E',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383245'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 10},
                                  'BSN': 'GB8926V7X3      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.160',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'QLogic QMH2462 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:aa:cc'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:10:a0:00:19:aa:ce'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 10},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 10}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 10},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 10},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 10},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 10}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:54:E0',
                                                                             'iSCSI': '00:25:B3:A3:54:E1'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:54:E4',
                                                                             'iSCSI': '00:25:B3:A3:54:E5'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 10},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 10}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 225},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 24,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V7X3',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656375833'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 11},
                                  'BSN': 'GB8926V81D      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.161',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:fc:24'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:fc:25'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 11},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 11}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 11},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 11},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 11},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 11}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AE:F1:78',
                                                                             'iSCSI': '00:24:81:AE:F1:79'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AE:F1:7C',
                                                                             'iSCSI': '00:24:81:AE:F1:7D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 11},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 11}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 228},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 26,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V81D',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383144'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 12},
                                  'BSN': 'GB8926V800      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.162',
                                  'PORTMAP': {'MEZZ': [{'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 12},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 12}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 12},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 12},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 12},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 12}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:15:20',
                                                                             'iSCSI': '00:25:B3:A3:15:21'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:15:24',
                                                                             'iSCSI': '00:25:B3:A3:15:25'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 12},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 12}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 193},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 26,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V800',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383030'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 13},
                                  'BSN': 'GB8926V7XT      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.163',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b4:2e'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b4:2f'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 13},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 13}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 13},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 13},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 13},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 13}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AD:DD:08',
                                                                             'iSCSI': '00:24:81:AD:DD:09'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:24:81:AD:DD:0C',
                                                                             'iSCSI': '00:24:81:AD:DD:0D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 13},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 13}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 239},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 25,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V7XT',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656375854'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 14},
                                  'BSN': 'GB8926V7XL      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.164',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b5:46'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:b5:47'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 14},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 14}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 14},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 14},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 14},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 14}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:7D:08',
                                                                             'iSCSI': '00:25:B3:A3:7D:09'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:7D:0C',
                                                                             'iSCSI': '00:25:B3:A3:7D:0D'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 14},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 14}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 489},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 23,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V7XL',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-32365637584C'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 15},
                                  'BSN': 'GB8926V7Y9      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.165',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'Emulex LPe1105-HP 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:99:cc'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '10:00:00:00:c9:81:99:cd'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 15},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 15}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 15},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 15},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 15},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 15}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:1C:A0',
                                                                             'iSCSI': '00:25:B3:A3:1C:A1'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:1C:A4',
                                                                             'iSCSI': '00:25:B3:A3:1C:A5'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 15},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 15}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 221},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 23,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V7Y9',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656375939'},
                                 {'ASSOCIATEDBLADE': 0,
                                  'BAY': {'CONNECTION': 16},
                                  'BSN': 'GB8926V80S      ',
                                  'CONJOINABLE': 'false',
                                  'DIAG': {'AC': 'NOT_RELEVANT',
                                           'Cooling': 'NO_ERROR',
                                           'Degraded': 'NO_ERROR',
                                           'FRU': 'NO_ERROR',
                                           'Failure': 'NO_ERROR',
                                           'Keying': 'NO_ERROR',
                                           'Location': 'NOT_TESTED',
                                           'MgmtProc': 'NO_ERROR',
                                           'Power': 'NO_ERROR',
                                           'i2c': 'NOT_RELEVANT',
                                           'oaRedundancy': 'NOT_RELEVANT',
                                           'thermalDanger': 'NOT_TESTED',
                                           'thermalWarning': 'NOT_TESTED'},
                                  'MANUFACTURER': 'HP',
                                  'MGMTIPADDR': '10.235.28.166',
                                  'PORTMAP': {'MEZZ': [{'DEVICE': {'NAME': 'QLogic QMH2462 4Gb FC HBA for HP c-Class BladeSystem',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:43:80:03:b9:ee:b0'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_FIB',
                                                                             'WWPN': '50:01:43:80:03:b9:ee:b2'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_ONE'},
                                                        'NUMBER': 1,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 3,
                                                                           'TRAYPORTNUMBER': 16},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 4,
                                                                           'TRAYPORTNUMBER': 16}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_ONE'}},
                                                       {'NUMBER': 2,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 5,
                                                                           'TRAYPORTNUMBER': 16},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 6,
                                                                           'TRAYPORTNUMBER': 16},
                                                                          {'NUMBER': 3,
                                                                           'TRAYBAYNUMBER': 7,
                                                                           'TRAYPORTNUMBER': 16},
                                                                          {'NUMBER': 4,
                                                                           'TRAYBAYNUMBER': 8,
                                                                           'TRAYPORTNUMBER': 16}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_TWO'}},
                                                       {'DEVICE': {'NAME': 'Flex-10 Embedded Ethernet',
                                                                   'PORT': [{'NUMBER': 1,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:83:90',
                                                                             'iSCSI': '00:25:B3:A3:83:91'},
                                                                            {'NUMBER': 2,
                                                                             'STATUS': 'OK',
                                                                             'TYPE': 'INTERCONNECT_TYPE_ETH',
                                                                             'WWPN': '00:25:B3:A3:83:94',
                                                                             'iSCSI': '00:25:B3:A3:83:95'}],
                                                                   'STATUS': 'OK',
                                                                   'TYPE': 'MEZZ_DEV_TYPE_FIXED'},
                                                        'NUMBER': 9,
                                                        'SLOT': {'PORT': [{'NUMBER': 1,
                                                                           'TRAYBAYNUMBER': 1,
                                                                           'TRAYPORTNUMBER': 16},
                                                                          {'NUMBER': 2,
                                                                           'TRAYBAYNUMBER': 2,
                                                                           'TRAYPORTNUMBER': 16}],
                                                                 'TYPE': 'MEZZ_SLOT_TYPE_FIXED'}}],
                                              'STATUS': 'OK'},
                                  'POWER': {'POWERMODE': 'UNKNOWN',
                                            'POWERSTATE': 'ON',
                                            'POWER_CONSUMED': 232},
                                  'SPN': 'ProLiant BL460c G6',
                                  'STATUS': 'OK',
                                  'TEMPS': {'TEMP': {'C': 24,
                                                     'DESC': 'AMBIENT',
                                                     'LOCATION': 14,
                                                     'THRESHOLD': [{'C': 42,
                                                                    'DESC': 'CAUTION',
                                                                    'STATUS': 'Degraded'},
                                                                   {'C': 46,
                                                                    'DESC': 'CRITICAL',
                                                                    'STATUS': 'Non-Recoverable Error'}]}},
                                  'TYPE': 'SERVER',
                                  'UIDSTATUS': 'OFF',
                                  'UUID': '507864GB8926V80S',
                                  'VMSTAT': {'CDROMSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'CDROMURL': Null,
                                             'FLOPPYSTAT': 'VM_DEV_STATUS_DISCONNECTED',
                                             'FLOPPYURL': Null,
                                             'SUPPORT': 'VM_SUPPORTED'},
                                  'cUUID': '38373035-3436-4247-3839-323656383053'}]},
            'DATETIME': datetime.datetime(2012, 7, 11, 19, 6, 20),
            'DIAG': {'AC': 'NOT_RELEVANT',
                     'Cooling': 'NOT_RELEVANT',
                     'Degraded': 'NOT_TESTED',
                     'FRU': 'NO_ERROR',
                     'Failure': 'NOT_TESTED',
                     'Keying': 'NOT_RELEVANT',
                     'Location': 'NOT_RELEVANT',
                     'MgmtProc': 'NOT_RELEVANT',
                     'Power': 'NOT_RELEVANT',
                     'i2c': 'NOT_RELEVANT',
                     'oaRedundancy': 'NO_ERROR',
                     'thermalDanger': 'NOT_RELEVANT',
                     'thermalWarning': 'NOT_RELEVANT'},
            'DIM': {'mmDepth': 756, 'mmHeight': 445, 'mmWidth': 444},
            'ENCL': 'HP_Blade_208-3',
            'ENCL_SN': '9B8925V2C9',
            'FANS': {'BAYS': {'BAY': [{'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 20,
                                       'mmYOffset': 0},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 98,
                                       'mmYOffset': 0},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 176,
                                       'mmYOffset': 0},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 254,
                                       'mmYOffset': 0},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 332,
                                       'mmYOffset': 0},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 20,
                                       'mmYOffset': 261},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 98,
                                       'mmYOffset': 261},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 176,
                                       'mmYOffset': 261},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 254,
                                       'mmYOffset': 261},
                                      {'SIDE': 'REAR',
                                       'mmDepth': 194,
                                       'mmHeight': 93,
                                       'mmWidth': 78,
                                       'mmXOffset': 332,
                                       'mmYOffset': 261}]},
                     'FAN': [{'BAY': {'CONNECTION': 1},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 17,
                              'RPM_CUR': 8498,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 2},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 15,
                              'RPM_CUR': 8499,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 3},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 20,
                              'RPM_CUR': 8500,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 4},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 13,
                              'RPM_CUR': 8300,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 5},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 20,
                              'RPM_CUR': 8300,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 6},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 12,
                              'RPM_CUR': 7000,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 7},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 10,
                              'RPM_CUR': 7000,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 8},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 12,
                              'RPM_CUR': 7160,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 9},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 10,
                              'RPM_CUR': 7147,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'},
                             {'BAY': {'CONNECTION': 10},
                              'PN': '412140-B21',
                              'PRODUCTNAME': 'Active Cool 200 Fan',
                              'PWR_USED': 11,
                              'RPM_CUR': 7160,
                              'RPM_MAX': 18000,
                              'RPM_MIN': 10,
                              'STATUS': 'OK'}],
                     'NEEDED_FANS': 9,
                     'REDUNDANCY': 'REDUNDANT',
                     'STATUS': 'OK',
                     'WANTED_FANS': 10},
            'LCDS': {'BAYS': {'BAY': {'SIDE': 'FRONT',
                                      'mmDepth': 15,
                                      'mmHeight': 55,
                                      'mmWidth': 92,
                                      'mmXOffset': 145,
                                      'mmYOffset': 365}},
                     'LCD': {'BAY': {'CONNECTION': 1},
                             'BUTTON_LOCK_ENABLED': 'false',
                             'DIAG': {'AC': 'NOT_RELEVANT',
                                      'Cooling': 'NOT_RELEVANT',
                                      'Degraded': 'NOT_TESTED',
                                      'FRU': 'NO_ERROR',
                                      'Failure': 'NOT_TESTED',
                                      'Keying': 'NOT_RELEVANT',
                                      'Location': 'NOT_RELEVANT',
                                      'MgmtProc': 'NOT_RELEVANT',
                                      'Power': 'NOT_RELEVANT',
                                      'i2c': 'NOT_RELEVANT',
                                      'oaRedundancy': 'NOT_RELEVANT',
                                      'thermalDanger': 'NOT_RELEVANT',
                                      'thermalWarning': 'NOT_RELEVANT'},
                             'FWRI': '2.2.2',
                             'IMAGE_URL': '/cgi-bin/getLCDImage?oaSessionKey=',
                             'MANUFACTURER': 'HP',
                             'PIN_ENABLED': 'false',
                             'PN': '441203-001',
                             'SPN': 'BladeSystem c7000 Insight Display',
                             'STATUS': 'OK',
                             'USERNOTES': 'Touch my^balls^^^^'}},
            'MANAGERS': {'BAYS': {'BAY': [{'SIDE': 'REAR',
                                           'mmDepth': 177,
                                           'mmHeight': 21,
                                           'mmWidth': 160,
                                           'mmXOffset': 0,
                                           'mmYOffset': 225},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 177,
                                           'mmHeight': 21,
                                           'mmWidth': 160,
                                           'mmXOffset': 255,
                                           'mmYOffset': 225}]},
                         'MANAGER': [{'BAY': {'CONNECTION': 1},
                                      'BSN': 'OB93BP1773    ',
                                      'DIAG': {'AC': 'NOT_RELEVANT',
                                               'Cooling': 'NOT_RELEVANT',
                                               'Degraded': 'NOT_TESTED',
                                               'FRU': 'NO_ERROR',
                                               'Failure': 'NOT_TESTED',
                                               'Keying': 'NOT_RELEVANT',
                                               'Location': 'NOT_RELEVANT',
                                               'MgmtProc': 'NOT_TESTED',
                                               'Power': 'NOT_RELEVANT',
                                               'i2c': 'NOT_RELEVANT',
                                               'oaRedundancy': 'NOT_TESTED',
                                               'thermalDanger': 'NOT_RELEVANT',
                                               'thermalWarning': 'NOT_RELEVANT'},
                                      'FWRI': 3.32,
                                      'IPV6STATUS': 'DISABLED',
                                      'MACADDR': '00:24:81:A4:3D:A9',
                                      'MANUFACTURER': 'HP',
                                      'MGMTIPADDR': '10.235.28.31',
                                      'NAME': 'OA-002481A43DA9',
                                      'POWER': {'POWERSTATE': 'ON'},
                                      'ROLE': 'ACTIVE',
                                      'SPN': 'BladeSystem c7000 DDR2 Onboard Administrator with KVM',
                                      'STATUS': 'OK',
                                      'TEMPS': {'TEMP': {'C': 41,
                                                         'DESC': 'AMBIENT',
                                                         'LOCATION': 17,
                                                         'THRESHOLD': [{'C': 75,
                                                                        'DESC': 'CAUTION',
                                                                        'STATUS': 'Degraded'},
                                                                       {'C': 80,
                                                                        'DESC': 'CRITICAL',
                                                                        'STATUS': 'Non-Recoverable Error'}]}},
                                      'UIDSTATUS': 'OFF',
                                      'UUID': '09OB93BP1773    ',
                                      'WIZARDSTATUS': 'WIZARD_SETUP_COMPLETE',
                                      'YOUAREHERE': 'true'},
                                     {'BAY': {'CONNECTION': 2},
                                      'BSN': 'OB94BP2794    ',
                                      'DIAG': {'AC': 'NOT_RELEVANT',
                                               'Cooling': 'NOT_RELEVANT',
                                               'Degraded': 'NOT_TESTED',
                                               'FRU': 'NO_ERROR',
                                               'Failure': 'NOT_TESTED',
                                               'Keying': 'NOT_RELEVANT',
                                               'Location': 'NOT_RELEVANT',
                                               'MgmtProc': 'NOT_TESTED',
                                               'Power': 'NOT_RELEVANT',
                                               'i2c': 'NOT_RELEVANT',
                                               'oaRedundancy': 'NOT_TESTED',
                                               'thermalDanger': 'NOT_RELEVANT',
                                               'thermalWarning': 'NOT_RELEVANT'},
                                      'FWRI': 3.32,
                                      'IPV6STATUS': 'DISABLED',
                                      'MACADDR': '00:24:81:AE:28:3B',
                                      'MANUFACTURER': 'HP',
                                      'MGMTIPADDR': '10.235.28.32',
                                      'NAME': 'OA-002481AE283B',
                                      'POWER': {'POWERSTATE': 'ON'},
                                      'ROLE': 'STANDBY',
                                      'SPN': 'BladeSystem c7000 DDR2 Onboard Administrator with KVM',
                                      'STATUS': 'OK',
                                      'TEMPS': {'TEMP': {'C': 42,
                                                         'DESC': 'AMBIENT',
                                                         'LOCATION': 17,
                                                         'THRESHOLD': [{'C': 75,
                                                                        'DESC': 'CAUTION',
                                                                        'STATUS': 'Degraded'},
                                                                       {'C': 80,
                                                                        'DESC': 'CRITICAL',
                                                                        'STATUS': 'Non-Recoverable Error'}]}},
                                      'UIDSTATUS': 'OFF',
                                      'UUID': '09OB94BP2794    ',
                                      'WIZARDSTATUS': 'WIZARD_SETUP_COMPLETE',
                                      'YOUAREHERE': 'false'}]},
            'PART': '507019-B21',
            'PN': 'BladeSystem c7000 Enclosure G2',
            'POWER': {'BAYS': {'BAY': [{'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 0,
                                        'mmYOffset': 365},
                                       {'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 70,
                                        'mmYOffset': 365},
                                       {'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 140,
                                        'mmYOffset': 365},
                                       {'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 210,
                                        'mmYOffset': 365},
                                       {'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 280,
                                        'mmYOffset': 365},
                                       {'SIDE': 'FRONT',
                                        'mmDepth': 700,
                                        'mmHeight': 56,
                                        'mmWidth': 70,
                                        'mmXOffset': 350,
                                        'mmYOffset': 365}]},
                      'CAPACITY': 7200,
                      'DYNAMICPOWERSAVER': 'true',
                      'NEEDED_PS': 2,
                      'OUTPUT_POWER': 12228,
                      'PDU': '413374-B21',
                      'POWERONFLAG': 'false',
                      'POWERSUPPLY': [{'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 543,
                                       'BAY': {'CONNECTION': 1},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLWY1Q5',
                                       'STATUS': 'OK'},
                                      {'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 543,
                                       'BAY': {'CONNECTION': 2},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLX10GO',
                                       'STATUS': 'OK'},
                                      {'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 0,
                                       'BAY': {'CONNECTION': 3},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLX11UY',
                                       'STATUS': 'OK'},
                                      {'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 543,
                                       'BAY': {'CONNECTION': 4},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLX11WW',
                                       'STATUS': 'OK'},
                                      {'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 543,
                                       'BAY': {'CONNECTION': 5},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLX10DK',
                                       'STATUS': 'OK'},
                                      {'ACINPUT': 'OK',
                                       'ACTUALOUTPUT': 0,
                                       'BAY': {'CONNECTION': 6},
                                       'CAPACITY': 2400,
                                       'DIAG': {'AC': 'NO_ERROR',
                                                'Cooling': 'NOT_RELEVANT',
                                                'Degraded': 'NOT_TESTED',
                                                'FRU': 'NO_ERROR',
                                                'Failure': 'NO_ERROR',
                                                'Keying': 'NOT_RELEVANT',
                                                'Location': 'NOT_TESTED',
                                                'MgmtProc': 'NOT_RELEVANT',
                                                'Power': 'NOT_RELEVANT',
                                                'i2c': 'NOT_RELEVANT',
                                                'oaRedundancy': 'NOT_RELEVANT',
                                                'thermalDanger': 'NOT_RELEVANT',
                                                'thermalWarning': 'NOT_RELEVANT'},
                                       'FWRI': 0.0,
                                       'PN': '499253-B21',
                                       'SN': '5AGUD0AHLWY1Y7',
                                       'STATUS': 'OK'}],
                      'POWER_CONSUMED': 4691,
                      'REDUNDANCY': 'REDUNDANT',
                      'REDUNDANCYMODE': 'AC_REDUNDANT',
                      'REDUNDANT_CAPACITY': 2509,
                      'STATUS': 'OK',
                      'TYPE': 'INTERNAL_DC',
                      'WANTED_PS': 4},
            'RACK': 'Rack_208',
            'SOLUTIONSID': 0,
            'STATUS': 'OK',
            'SWITCHES': {'BAYS': {'BAY': [{'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 0,
                                           'mmYOffset': 95},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 193,
                                           'mmYOffset': 95},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 0,
                                           'mmYOffset': 123},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 193,
                                           'mmYOffset': 123},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 0,
                                           'mmYOffset': 151},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 193,
                                           'mmYOffset': 151},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 0,
                                           'mmYOffset': 179},
                                          {'SIDE': 'REAR',
                                           'mmDepth': 268,
                                           'mmHeight': 28,
                                           'mmWidth': 193,
                                           'mmXOffset': 193,
                                           'mmYOffset': 179}]},
                         'SWITCH': [{'BAY': {'CONNECTION': 1},
                                     'BSN': 'FOC1316T07G',
                                     'DIAG': {'AC': 'NOT_RELEVANT',
                                              'Cooling': 'NOT_RELEVANT',
                                              'Degraded': 'NO_ERROR',
                                              'FRU': 'NO_ERROR',
                                              'Failure': 'NO_ERROR',
                                              'Keying': 'NO_ERROR',
                                              'Location': 'NOT_RELEVANT',
                                              'MgmtProc': 'NOT_TESTED',
                                              'Power': 'NO_ERROR',
                                              'i2c': 'NOT_RELEVANT',
                                              'oaRedundancy': 'NOT_RELEVANT',
                                              'thermalDanger': 'NO_ERROR',
                                              'thermalWarning': 'NO_ERROR'},
                                     'FABRICTYPE': 'INTERCONNECT_TYPE_ETH',
                                     'FAULT': 'CPUFAULT',
                                     'MANUFACTURER': 'Cisco Systems, Inc.',
                                     'MGMTIPADDR': '10.235.28.33',
                                     'MGMTURL': 'http://10.235.28.33',
                                     'PORTMAP': {'PASSTHRU_MODE_ENABLED': 'DISABLED',
                                                 'SLOT': {'NUMBER': 1,
                                                          'PORT': [{'BLADEBAYNUMBER': 1,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 1,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 2,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 2,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 3,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 3,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 4,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 4,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 5,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 5,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 6,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 6,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 7,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 7,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 8,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 8,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 9,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 9,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 10,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 10,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 11,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 11,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 12,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 12,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 13,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 13,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 14,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 14,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 15,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 15,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 16,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 16,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'}],
                                                          'TYPE': 'INTERCONNECT_TYPE_ETH'},
                                                 'STATUS': 'OK'},
                                     'POWER': {'POWERSTATE': 'ON',
                                               'POWER_OFF_WATTAGE': 2,
                                               'POWER_ON_WATTAGE': 60},
                                     'SPN': 'Cisco Catalyst Blade Switch 3020 for HP',
                                     'STATUS': 'OK',
                                     'TEMPS': {'TEMP': {'C': 0,
                                                        'DESC': 'AMBIENT',
                                                        'LOCATION': 13,
                                                        'THRESHOLD': [{'C': 0,
                                                                       'DESC': 'CAUTION',
                                                                       'STATUS': 'Degraded'},
                                                                      {'C': 0,
                                                                       'DESC': 'CRITICAL',
                                                                       'STATUS': 'Non-Recoverable Error'}]}},
                                     'THERMAL': 'OK',
                                     'UIDSTATUS': 'OFF'},
                                    {'BAY': {'CONNECTION': 2},
                                     'BSN': 'FOC1316T0D6',
                                     'DIAG': {'AC': 'NOT_RELEVANT',
                                              'Cooling': 'NOT_RELEVANT',
                                              'Degraded': 'NO_ERROR',
                                              'FRU': 'NO_ERROR',
                                              'Failure': 'NO_ERROR',
                                              'Keying': 'NO_ERROR',
                                              'Location': 'NOT_RELEVANT',
                                              'MgmtProc': 'NOT_TESTED',
                                              'Power': 'NO_ERROR',
                                              'i2c': 'NOT_RELEVANT',
                                              'oaRedundancy': 'NOT_RELEVANT',
                                              'thermalDanger': 'NO_ERROR',
                                              'thermalWarning': 'NO_ERROR'},
                                     'FABRICTYPE': 'INTERCONNECT_TYPE_ETH',
                                     'FAULT': 'CPUFAULT',
                                     'MANUFACTURER': 'Cisco Systems, Inc.',
                                     'MGMTIPADDR': '10.235.28.34',
                                     'MGMTURL': 'http://10.235.28.34',
                                     'PORTMAP': {'PASSTHRU_MODE_ENABLED': 'DISABLED',
                                                 'SLOT': {'NUMBER': 1,
                                                          'PORT': [{'BLADEBAYNUMBER': 1,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 1,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 2,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 2,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 3,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 3,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 4,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 4,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 5,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 5,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 6,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 6,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 7,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 7,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 8,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 8,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 9,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 9,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 10,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 10,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 11,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 11,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 12,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 12,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 13,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 13,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 14,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 14,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 15,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 15,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 16,
                                                                    'BLADEMEZZNUMBER': 9,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 16,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'}],
                                                          'TYPE': 'INTERCONNECT_TYPE_ETH'},
                                                 'STATUS': 'OK'},
                                     'POWER': {'POWERSTATE': 'ON',
                                               'POWER_OFF_WATTAGE': 2,
                                               'POWER_ON_WATTAGE': 60},
                                     'SPN': 'Cisco Catalyst Blade Switch 3020 for HP',
                                     'STATUS': 'OK',
                                     'TEMPS': {'TEMP': {'C': 0,
                                                        'DESC': 'AMBIENT',
                                                        'LOCATION': 13,
                                                        'THRESHOLD': [{'C': 0,
                                                                       'DESC': 'CAUTION',
                                                                       'STATUS': 'Degraded'},
                                                                      {'C': 0,
                                                                       'DESC': 'CRITICAL',
                                                                       'STATUS': 'Non-Recoverable Error'}]}},
                                     'THERMAL': 'OK',
                                     'UIDSTATUS': 'OFF'},
                                    {'BAY': {'CONNECTION': 3},
                                     'BSN': 'CN89197024',
                                     'DIAG': {'AC': 'NOT_RELEVANT',
                                              'Cooling': 'NOT_RELEVANT',
                                              'Degraded': 'NO_ERROR',
                                              'FRU': 'NO_ERROR',
                                              'Failure': 'NO_ERROR',
                                              'Keying': 'NO_ERROR',
                                              'Location': 'NOT_RELEVANT',
                                              'MgmtProc': 'NO_ERROR',
                                              'Power': 'NO_ERROR',
                                              'i2c': 'NOT_RELEVANT',
                                              'oaRedundancy': 'NOT_RELEVANT',
                                              'thermalDanger': 'NO_ERROR',
                                              'thermalWarning': 'NO_ERROR'},
                                     'FABRICTYPE': 'INTERCONNECT_TYPE_FIB',
                                     'MANUFACTURER': 'BROCADE',
                                     'MGMTIPADDR': '10.235.28.35',
                                     'MGMTURL': 'http://10.235.28.35',
                                     'PORTMAP': {'PASSTHRU_MODE_ENABLED': 'DISABLED',
                                                 'SLOT': {'NUMBER': 1,
                                                          'PORT': [{'BLADEBAYNUMBER': 1,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 1,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 2,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 3,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 3,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 4,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 5,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 5,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 6,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 7,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 8,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 8,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 9,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 9,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 10,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 10,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 11,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 11,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 12,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 13,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 13,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 14,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 14,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 15,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 15,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 16,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 1,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 16,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'}],
                                                          'TYPE': 'INTERCONNECT_TYPE_FIB'},
                                                 'STATUS': 'OK'},
                                     'POWER': {'POWERSTATE': 'ON',
                                               'POWER_OFF_WATTAGE': 1,
                                               'POWER_ON_WATTAGE': 35},
                                     'SPN': 'Brocade 4/24 SAN Switch for HP c-Class BladeSystem',
                                     'STATUS': 'OK',
                                     'TEMPS': {'TEMP': {'C': 0,
                                                        'DESC': 'AMBIENT',
                                                        'LOCATION': 13,
                                                        'THRESHOLD': [{'C': 0,
                                                                       'DESC': 'CAUTION',
                                                                       'STATUS': 'Degraded'},
                                                                      {'C': 0,
                                                                       'DESC': 'CRITICAL',
                                                                       'STATUS': 'Non-Recoverable Error'}]}},
                                     'THERMAL': 'OK',
                                     'UIDSTATUS': 'OFF'},
                                    {'BAY': {'CONNECTION': 4},
                                     'BSN': 'CN89207019',
                                     'DIAG': {'AC': 'NOT_RELEVANT',
                                              'Cooling': 'NOT_RELEVANT',
                                              'Degraded': 'NO_ERROR',
                                              'FRU': 'NO_ERROR',
                                              'Failure': 'NO_ERROR',
                                              'Keying': 'NO_ERROR',
                                              'Location': 'NOT_RELEVANT',
                                              'MgmtProc': 'NO_ERROR',
                                              'Power': 'NO_ERROR',
                                              'i2c': 'NOT_RELEVANT',
                                              'oaRedundancy': 'NOT_RELEVANT',
                                              'thermalDanger': 'NO_ERROR',
                                              'thermalWarning': 'NO_ERROR'},
                                     'FABRICTYPE': 'INTERCONNECT_TYPE_FIB',
                                     'MANUFACTURER': 'BROCADE',
                                     'MGMTIPADDR': '10.235.28.36',
                                     'MGMTURL': 'http://10.235.28.36',
                                     'PORTMAP': {'PASSTHRU_MODE_ENABLED': 'DISABLED',
                                                 'SLOT': {'NUMBER': 1,
                                                          'PORT': [{'BLADEBAYNUMBER': 1,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 1,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 2,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 3,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 3,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 4,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 5,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 5,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 6,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 7,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 8,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 8,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 9,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 9,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 10,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 10,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 11,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 11,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 0,
                                                                    'BLADEMEZZNUMBER': 0,
                                                                    'BLADEMEZZPORTNUMBER': 0,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 12,
                                                                    'STATUS': 'UNKNOWN',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 13,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 13,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 14,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 14,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 15,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 15,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'},
                                                                   {'BLADEBAYNUMBER': 16,
                                                                    'BLADEMEZZNUMBER': 1,
                                                                    'BLADEMEZZPORTNUMBER': 2,
                                                                    'ENABLED': 'UNKNOWN',
                                                                    'LINK_LED_STATUS': 'UNKNOWN',
                                                                    'NUMBER': 16,
                                                                    'STATUS': 'OK',
                                                                    'UID_STATUS': 'UNKNOWN'}],
                                                          'TYPE': 'INTERCONNECT_TYPE_FIB'},
                                                 'STATUS': 'OK'},
                                     'POWER': {'POWERSTATE': 'ON',
                                               'POWER_OFF_WATTAGE': 1,
                                               'POWER_ON_WATTAGE': 35},
                                     'SPN': 'Brocade 4/24 SAN Switch for HP c-Class BladeSystem',
                                     'STATUS': 'OK',
                                     'TEMPS': {'TEMP': {'C': 0,
                                                        'DESC': 'AMBIENT',
                                                        'LOCATION': 13,
                                                        'THRESHOLD': [{'C': 0,
                                                                       'DESC': 'CAUTION',
                                                                       'STATUS': 'Degraded'},
                                                                      {'C': 0,
                                                                       'DESC': 'CRITICAL',
                                                                       'STATUS': 'Non-Recoverable Error'}]}},
                                     'THERMAL': 'OK',
                                     'UIDSTATUS': 'OFF'}]},
            'TEMPS': {'TEMP': {'C': 26,
                               'DESC': 'AMBIENT',
                               'LOCATION': 9,
                               'THRESHOLD': [{'C': 42,
                                              'DESC': 'CAUTION',
                                              'STATUS': 'Degraded'},
                                             {'C': 46,
                                              'DESC': 'CRITICAL',
                                              'STATUS': 'Non-Recoverable Error'}]}},
            'TIMEZONE': 'Europe/Warsaw',
            'UIDSTATUS': 'OFF',
            'UUID': '09GB8925V2C9',
            'VCM': {'vcmDomainId': Null,
                    'vcmDomainName': Null,
                    'vcmMode': 'false',
                    'vcmUrl': 'empty'},
            'VM': {'DVDDRIVE': 'ABSENT'}},
 'MP': {'CIMOM': 'false',
        'FWRI': 3.32,
        'HWRI': 65.5,
        'PN': 'BladeSystem c7000 DDR2 Onboard Administrator with KVM',
        'PRIM': 'true',
        'SN': 'OB93BP1773    ',
        'SSO': 'false',
        'ST': 1,
        'STE': 'false',
        'USESTE': 'false',
        'UUID': '09OB93BP1773    '},
 'RK_TPLGY': {'ICMB': {'LEFT': Null, 'RIGHT': Null}, 'RUID': '09GB8925V2C9'}}

    def test_encl(self):
        encl = hp_oa.make_encl(self.DATA, '')
        self.assertEquals(encl.name, '')
        self.assertEquals(encl.sn, '9B8925V2C9')
        self.assertEquals(encl.model.type, DeviceType.blade_system.id)
        self.assertEquals(encl.model.name, 'HP BladeSystem c7000 Enclosure G2')


    def test_devices(self):
        encl = hp_oa.make_encl(self.DATA, '')
        data = nullify(self.DATA)
        hp_oa._add_hp_oa_devices(data['INFRA2']['MANAGERS']['MANAGER'],
            DeviceType.management, parent=encl)
        hp_oa._add_hp_oa_devices(data['INFRA2']['SWITCHES']['SWITCH'],
            DeviceType.switch, parent=encl)
        hp_oa._add_hp_oa_devices(data['INFRA2']['BLADES']['BLADE'],
            DeviceType.blade_server, parent=encl)
        models = [d.model.name for d in encl.child_set.all()]
        self.maxDiff = None
        self.assertEqual(models, [
            'HP Cisco Catalyst Blade Switch 3020 for HP',
            'HP Cisco Catalyst Blade Switch 3020 for HP',
            'HP Brocade 4/24 SAN Switch for HP c-Class BladeSystem',
            'HP Brocade 4/24 SAN Switch for HP c-Class BladeSystem',
            'HP ProLiant BL460c G1',
            'HP ProLiant BL460c G1',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G1',
            'HP ProLiant BL460c G1',
            'HP ProLiant BL460c G1',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
            'HP ProLiant BL460c G6',
        ])
        macs = [[e.mac for e in d.ethernet_set.all()] for d in encl.child_set.all()]
        self.assertEqual(macs, [
            [],
            [],
            [],
            [],
            ['0022649C6FF6', '0022649C7F42'],
            ['001A4BD0CC0E', '001A4BD0DC14'],
            ['0025B3A31468', '0025B3A3146C'],
            ['00237DA92A70', '00237DA92A76'],
            ['001A4BD0B564', '001A4BD0B570'],
            ['00237DA92BB0', '00237DA92BB2'],
            ['002481AEC098', '002481AEC09C'],
            ['0025B3A36D38', '0025B3A36D3C'],
            ['0025B3A3A288', '0025B3A3A28C'],
            ['0025B3A354E0', '0025B3A354E4'],
            ['002481AEF178', '002481AEF17C'],
            ['0025B3A31520', '0025B3A31524'],
            ['002481ADDD08', '002481ADDD0C'],
            ['0025B3A37D08', '0025B3A37D0C'],
            ['0025B3A31CA0', '0025B3A31CA4'],
            ['0025B3A38390', '0025B3A38394'],
        ])
        positions = [d.position for d in encl.child_set.all()]
        self.assertEqual(positions, ['1', '2', '3', '4', '1', '2', '3', '4',
            '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16'])


class SnmpPluginTest(TestCase):
    def test_name(self):
        ip = IPAddress(address='127.0.0.1')
        ip.save()
        with mock.patch('ralph.util.network.snmp') as network_snmp:
            network_snmp.return_value = [[None, b'Testing name']]
            is_up, message = snmp._snmp('127.0.0.1', 'public', (1,3,6,1,2,1,1,1,0))
        self.assertEqual(message, 'Testing name')
        self.assertEqual(is_up, True)

    def test_noip(self):
        with mock.patch('ralph.util.network.snmp') as network_snmp:
            network_snmp.return_value = [[None, b'Testing name']]
            is_up, message = snmp._snmp('127.0.0.1', 'public', (1,3,6,1,2,1,1,1,0))
        self.assertEqual(message, 'IP address not present in DB.')
        self.assertEqual(is_up, False)

    def test_silent(self):
        with mock.patch('ralph.util.network.snmp') as network_snmp:
            network_snmp.return_value = None
            is_up, message = snmp._snmp('127.0.0.1', 'public', (1,3,6,1,2,1,1,1,0))
        self.assertEqual(message, 'silent.')
        self.assertEqual(is_up, False)


class SnmpMacPluginTest(TestCase):
    def setUp(self):
        ip = IPAddress(address='127.0.0.1')
        ip.snmp_name = ('Hardware: EM64T Family 6 Model 15 Stepping 7 AT/AT '
                        'COMPATIBLE - Software: Windows Version 5.2 (Build '
                        '3790 Multiprocessor Free)')
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

    def tearDown(self):
        self.ip.delete()

    def test_windows(self):
        with mock.patch('ralph.util.network.snmp_macs') as network_snmp_macs:
            network_snmp_macs.return_value = ['001A643320EA']
            ethernets = snmp.do_snmp_mac(self.ip.snmp_name,
                                         self.ip.snmp_community,
                                         self.ip.snmp_version, self.ip.address,
                                         self.kwargs)
        macs = [e.mac for e in ethernets]
        self.assertEquals(macs, ['001A643320EA'])
        ip = IPAddress.objects.get(address=self.ip.address)
        self.assertEquals(ip.is_management, False)
        dev = ip.device
        self.assertNotEquals(dev, None)
        self.assertEquals(dev.model.name, 'Windows')
        self.assertEquals(dev.model.type, DeviceType.unknown.id)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEquals(macs, ['001A643320EA'])

    def test_windows_empty(self):
        with mock.patch('ralph.util.network.snmp_macs') as network_snmp_macs:
            network_snmp_macs.return_value = []
            with self.assertRaises(snmp.Error) as raised:
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                                 self.ip.snmp_version, self.ip.address,
                                 self.kwargs)
            self.assertEquals(raised.exception.message, 'no MAC.')

    def test_f5(self):
        self.ip.snmp_name = ('Linux f5-2a.dc2 2.6.18-164.11.1.el5.1.0.f5app #1 '
                             'SMP Mon Oct 18 11:55:00 PDT 2010 x86_64')
        self.ip.save()
        def snmp_side(ip, community, oid, *args, **kwargs):
            oid = '.'.join(str(i) for i in oid)
            if oid == '1.3.6.1.4.1.3375.2.1.3.5.2.0':
                return [[None, 'F5 BIG-IP 8400']]
            elif oid == '1.3.6.1.4.1.3375.2.1.3.3.3.0':
                return [[None, 'bip241990s']]
        with mock.patch('ralph.util.network.snmp_macs') as network_snmp_macs:
            network_snmp_macs.return_value = ['0001D76A7852', '0001D76A7846',
                '0001D76A784A', '0001D76A784E', '0001D76A7843', '0001D76A7847',
                '0001D76A784B', '0001D76A784F', '0001D76A7844', '0001D76A7848',
                '0001D76A784C', '0001D76A7850', '00D06814F5F6', '0001D76A7845',
                '0001D76A7849', '0001D76A784D', '0001D76A7851', '0201D76A7851']
            with mock.patch('ralph.util.network.snmp') as network_snmp:
                network_snmp.side_effect = snmp_side
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                                 self.ip.snmp_version, self.ip.address,
                                 self.kwargs)
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertNotIn('0201D76A7851', macs, "Filtering F5 shared MACs.")

    def test_vmware(self):
        self.ip.snmp_name = ('VMware ESX 4.1.0 build-320137 VMware, Inc. '
                             'x86_64')
        self.ip.save()
        def macs_side(ip, community, oid, *args, **kwargs):
            if oid == (1,3,6,1,4,1,6876,2,4,1,7):
                return ['000C2942346D']
            return ['1CC1DEEC0FEC', '1CC1DEEC0FE8']

        with mock.patch('ralph.util.network.snmp_macs') as network_snmp_macs:
            network_snmp_macs.side_effect = macs_side
            snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                             self.ip.snmp_version, self.ip.address, self.kwargs)
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        children = [d.model.name for d in dev.child_set.all()]
        self.assertEqual(children, ['VMware ESX virtual server'])
        macs = [[e.mac for e in d.ethernet_set.all()] for d in dev.child_set.all()]
        self.assertEqual(macs, [['000C2942346D']])

    def test_modular(self):
        self.ip.snmp_name = 'Intel Modular Server System'
        self.ip.save()
        def macs_side(ip, community, oid, *args, **kwargs):
            soid = '.'.join(str(i) for i in oid)
            if soid.startswith('1.3.6.1.4.1.343.2.19.1.2.10.202.3.1.1.'):
                return {
                    1: set([u'001E670C5960', u'001E67123169', u'001E67123168',
                            u'001E670C5961', u'001E670C53BD', u'001E6710DD9D',
                            u'001E6710DD9C', u'001E670C53BC', u'001E671232F5',
                            u'001E671232F4', u'001E670C5395', u'001E670C5394']),
                    2: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                            u'001E671232F5', u'001E671232F4', u'001E670C5395',
                            u'001E670C5394']),
                    3: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E6710DD9D', u'001E6710DD9C', u'001E670C53BC',
                            u'001E670C5395', u'001E670C5394']),
                    4: set([u'001E670C5960', u'001E670C5961', u'001E670C53BD',
                            u'001E670C53BC', u'001E670C5395', u'001E670C5394']),
                    5: set([u'001E670C5960', u'001E670C5961', u'001E670C5395',
                            u'001E670C5394']),
                    6: set([u'001E670C5960', u'001E670C5961'])
                }[oid[-1]]
            return ['001E6712C2E6', '001E6712C2E7']
        with mock.patch('ralph.util.network.snmp_macs') as network_snmp_macs:
            network_snmp_macs.side_effect = macs_side
            with mock.patch('ralph.util.network.snmp') as network_snmp:
                network_snmp.return_value = [[None, 6]]
                snmp.do_snmp_mac(self.ip.snmp_name, self.ip.snmp_community,
                             self.ip.snmp_version, self.ip.address, self.kwargs)
        self.maxDiff = None
        ip = IPAddress.objects.get(address=self.ip.address)
        dev = ip.device
        self.assertNotEquals(dev, None)
        children = [d.model.name for d in dev.child_set.all()]
        self.assertEqual(children, ['Intel Modular Blade'] * 6)
        macs = [[e.mac for e in d.ethernet_set.all()] for d in dev.child_set.all()]
        self.assertEqual(macs, [
            [u'001E67123168', u'001E67123169'],
            [u'001E671232F4', u'001E671232F5'],
            [u'001E6710DD9C', u'001E6710DD9D'],
            [u'001E670C53BC', u'001E670C53BD'],
            [u'001E670C5394', u'001E670C5395'],
            [u'001E670C5960', u'001E670C5961']
        ])

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
(u'lsattr -El sys0 | grep ^modelname', u'modelname       IBM,8233-E8B       Machine name                                      False\n'),
(u'netstat -ia | grep link', u'en0   9000  link#2      0.21.5e.e2.1b.50 576634574     0 573329335     0     0\nen1   9000  link#3      0.21.5e.e2.1b.52 576760839     0 572772320     0     0\nen2   9000  link#4      0.21.5e.e2.18.98 576767812     0 573362079     0     0\nen3   9000  link#5      0.21.5e.e2.18.9a 576726865     0 572257966     0     0\nen6   9000  link#6      0.21.5e.e2.2d.e0    93594     0  1209927     0     0\nen7   9000  link#7      0.21.5e.e2.2d.e2   100896     0  1202620     0     0\nen8   1500  link#8      e4.1f.13.4e.7e.8e 139058659     0 1505805421     6     0\nlo0   16896 link#1                       2342682952     0 2343897647     0     0\n'),
(u'lsdev -c disk', u'hdisk0  Available 04-08-00 SAS Disk Drive\nhdisk1  Available 04-08-00 SAS Disk Drive\nhdisk2  Available 04-08-00 SAS Disk Drive\nhdisk3  Available 04-08-00 SAS Disk Drive\nhdisk4  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk5  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk6  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk7  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk8  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk9  Available 08-00-02 3PAR InServ Virtual Volume\nhdisk10 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk11 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk12 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk13 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk14 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk15 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk16 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk17 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk18 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk19 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk20 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk21 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk22 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk23 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk24 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk25 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk26 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk27 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk28 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk29 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk30 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk31 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk32 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk33 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk34 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk35 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk36 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk37 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk38 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk39 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk40 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk41 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk42 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk43 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk44 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk45 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk46 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk47 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk48 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk49 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk50 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk51 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk52 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk53 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk54 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk55 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk56 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk57 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk58 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk59 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk60 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk61 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk62 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk63 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk64 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk65 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk66 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk67 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk68 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk69 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk70 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk71 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk72 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk73 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk74 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk75 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk76 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk77 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk78 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk79 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk80 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk81 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk82 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk83 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk84 Available 08-00-02 3PAR InServ Virtual Volume\nhdisk85 Available 08-00-02 3PAR InServ Virtual Volume\n'),
(u'lscfg -vl hdisk0', u'  hdisk0           U78A0.001.DNWK041-P2-D3  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RKYY\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F003002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D3\n\n'),
(u'lscfg -vl hdisk1', u'  hdisk1           U78A0.001.DNWK041-P2-D4  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RJQ2\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F001002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D4\n\n'),
(u'lscfg -vl hdisk2', u'  hdisk2           U78A0.001.DNWK041-P2-D5  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RJZS\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F003002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D5\n\n'),
(u'lscfg -vl hdisk3', u'  hdisk3           U78A0.001.DNWK041-P2-D6  SAS Disk Drive (146800 MB)\n\n        Manufacturer................IBM     \n        Machine Type and Model......ST9146852SS     \n        FRU Number..................44V6845     \n        ROS Level and ID............43413033\n        Serial Number...............3TB1RKYZ\n        EC Level....................L36403    \n        Part Number.................44V6843     \n        Device Specific.(Z0)........000005329F001002\n        Device Specific.(Z1)........0918CA03    \n        Device Specific.(Z2)........0021\n        Device Specific.(Z3)........10172\n        Device Specific.(Z4)........\n        Device Specific.(Z5)........22\n        Device Specific.(Z6)........L36403    \n        Hardware Location Code......U78A0.001.DNWK041-P2-D6\n\n'),
(u'lscfg -vl hdisk4', u'  hdisk4           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L0  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000090A9B5000\n\n'),
(u'lscfg -vl hdisk5', u'  hdisk5           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L1000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000A0A9B5000\n\n'),
(u'lscfg -vl hdisk6', u'  hdisk6           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000B0A9B5000\n\n'),
(u'lscfg -vl hdisk7', u'  hdisk7           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000C0A9B5000\n\n'),
(u'lscfg -vl hdisk8', u'  hdisk8           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000D0A9B5000\n\n'),
(u'lscfg -vl hdisk9', u'  hdisk9           U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L14000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0000F0A9B5000\n\n'),
(u'lscfg -vl hdisk10', u'  hdisk10          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000100A9B5000\n\n'),
(u'lscfg -vl hdisk11', u'  hdisk11          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L16000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000110A9B5000\n\n'),
(u'lscfg -vl hdisk12', u'  hdisk12          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L17000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000120A9B5000\n\n'),
(u'lscfg -vl hdisk13', u'  hdisk13          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L28000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000130A9B5000\n\n'),
(u'lscfg -vl hdisk14', u'  hdisk14          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L29000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000140A9B5000\n\n'),
(u'lscfg -vl hdisk15', u'  hdisk15          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L2A000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000150A9B5000\n\n'),
(u'lscfg -vl hdisk16', u'  hdisk16          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L2B000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000160A9B5000\n\n'),
(u'lscfg -vl hdisk17', u'  hdisk17          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000170A9B5000\n\n'),
(u'lscfg -vl hdisk18', u'  hdisk18          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000180A9B5000\n\n'),
(u'lscfg -vl hdisk19', u'  hdisk19          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000190A9B5000\n\n'),
(u'lscfg -vl hdisk20', u'  hdisk20          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L3F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001A0A9B5000\n\n'),
(u'lscfg -vl hdisk21', u'  hdisk21          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L50000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001B0A9B5000\n\n'),
(u'lscfg -vl hdisk22', u'  hdisk22          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L51000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001C0A9B5000\n\n'),
(u'lscfg -vl hdisk23', u'  hdisk23          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L52000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001D0A9B5000\n\n'),
(u'lscfg -vl hdisk24', u'  hdisk24          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L53000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001E0A9B5000\n\n'),
(u'lscfg -vl hdisk25', u'  hdisk25          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L64000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0001F0A9B5000\n\n'),
(u'lscfg -vl hdisk26', u'  hdisk26          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L65000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000200A9B5000\n\n'),
(u'lscfg -vl hdisk27', u'  hdisk27          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L66000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000210A9B5000\n\n'),
(u'lscfg -vl hdisk28', u'  hdisk28          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L67000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000220A9B5000\n\n'),
(u'lscfg -vl hdisk29', u'  hdisk29          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L68000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000230A9B5000\n\n'),
(u'lscfg -vl hdisk30', u'  hdisk30          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L69000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000240A9B5000\n\n'),
(u'lscfg -vl hdisk31', u'  hdisk31          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L96000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002D0A9B5000\n\n'),
(u'lscfg -vl hdisk32', u'  hdisk32          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L97000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002E0A9B5000\n\n'),
(u'lscfg -vl hdisk33', u'  hdisk33          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L98000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002F0A9B5000\n\n'),
(u'lscfg -vl hdisk34', u'  hdisk34          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L99000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000300A9B5000\n\n'),
(u'lscfg -vl hdisk35', u'  hdisk35          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9A000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000310A9B5000\n\n'),
(u'lscfg -vl hdisk36', u'  hdisk36          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9B000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000320A9B5000\n\n'),
(u'lscfg -vl hdisk37', u'  hdisk37          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000330A9B5000\n\n'),
(u'lscfg -vl hdisk38', u'  hdisk38          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000340A9B5000\n\n'),
(u'lscfg -vl hdisk39', u'  hdisk39          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC8000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000250A9B5000\n\n'),
(u'lscfg -vl hdisk40', u'  hdisk40          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LC9000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000260A9B5000\n\n'),
(u'lscfg -vl hdisk41', u'  hdisk41          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000270A9B5000\n\n'),
(u'lscfg -vl hdisk42', u'  hdisk42          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000280A9B5000\n\n'),
(u'lscfg -vl hdisk43', u'  hdisk43          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000290A9B5000\n\n'),
(u'lscfg -vl hdisk44', u'  hdisk44          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCD000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002A0A9B5000\n\n'),
(u'lscfg -vl hdisk45', u'  hdisk45          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCE000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002B0A9B5000\n\n'),
(u'lscfg -vl hdisk46', u'  hdisk46          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LCF000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0002C0A9B5000\n\n'),
(u'lscfg -vl hdisk47', u'  hdisk47          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFA000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000350A9B5000\n\n'),
(u'lscfg -vl hdisk48', u'  hdisk48          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFB000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000360A9B5000\n\n'),
(u'lscfg -vl hdisk49', u'  hdisk49          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFC000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000370A9B5000\n\n'),
(u'lscfg -vl hdisk50', u'  hdisk50          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFD000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000380A9B5000\n\n'),
(u'lscfg -vl hdisk51', u'  hdisk51          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFE000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000390A9B5000\n\n'),
(u'lscfg -vl hdisk52', u'  hdisk52          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-LFF000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003A0A9B5000\n\n'),
(u'lscfg -vl hdisk53', u'  hdisk53          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12C000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000470A9B5000\n\n'),
(u'lscfg -vl hdisk54', u'  hdisk54          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12D000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000480A9B5000\n\n'),
(u'lscfg -vl hdisk55', u'  hdisk55          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000490A9B5000\n\n'),
(u'lscfg -vl hdisk56', u'  hdisk56          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L12F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004A0A9B5000\n\n'),
(u'lscfg -vl hdisk57', u'  hdisk57          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L130000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004B0A9B5000\n\n'),
(u'lscfg -vl hdisk58', u'  hdisk58          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L131000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004C0A9B5000\n\n'),
(u'lscfg -vl hdisk59', u'  hdisk59          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L132000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004D0A9B5000\n\n'),
(u'lscfg -vl hdisk60', u'  hdisk60          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L133000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004E0A9B5000\n\n'),
(u'lscfg -vl hdisk61', u'  hdisk61          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L134000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0004F0A9B5000\n\n'),
(u'lscfg -vl hdisk62', u'  hdisk62          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L135000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000500A9B5000\n\n'),
(u'lscfg -vl hdisk63', u'  hdisk63          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L136000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000510A9B5000\n\n'),
(u'lscfg -vl hdisk64', u'  hdisk64          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L137000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000520A9B5000\n\n'),
(u'lscfg -vl hdisk65', u'  hdisk65          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C60A9B5000\n\n'),
(u'lscfg -vl hdisk66', u'  hdisk66          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15E000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003B0A9B5000\n\n'),
(u'lscfg -vl hdisk67', u'  hdisk67          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L15F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003C0A9B5000\n\n'),
(u'lscfg -vl hdisk68', u'  hdisk68          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L160000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003D0A9B5000\n\n'),
(u'lscfg -vl hdisk69', u'  hdisk69          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L161000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003E0A9B5000\n\n'),
(u'lscfg -vl hdisk70', u'  hdisk70          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L162000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC0003F0A9B5000\n\n'),
(u'lscfg -vl hdisk71', u'  hdisk71          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L163000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000400A9B5000\n\n'),
(u'lscfg -vl hdisk72', u'  hdisk72          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L164000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000410A9B5000\n\n'),
(u'lscfg -vl hdisk73', u'  hdisk73          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L165000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000420A9B5000\n\n'),
(u'lscfg -vl hdisk74', u'  hdisk74          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L166000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000430A9B5000\n\n'),
(u'lscfg -vl hdisk75', u'  hdisk75          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L167000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000440A9B5000\n\n'),
(u'lscfg -vl hdisk76', u'  hdisk76          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L169000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000460A9B5000\n\n'),
(u'lscfg -vl hdisk77', u'  hdisk77          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L190000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000530A9B5000\n\n'),
(u'lscfg -vl hdisk78', u'  hdisk78          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L191000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000540A9B5000\n\n'),
(u'lscfg -vl hdisk79', u'  hdisk79          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L5000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C10A9B5000\n\n'),
(u'lscfg -vl hdisk80', u'  hdisk80          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L40000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C20A9B5000\n\n'),
(u'lscfg -vl hdisk81', u'  hdisk81          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L41000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C30A9B5000\n\n'),
(u'lscfg -vl hdisk82', u'  hdisk82          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L192000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C40A9B5000\n\n'),
(u'lscfg -vl hdisk83', u'  hdisk83          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L138000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000C50A9B5000\n\n'),
(u'lscfg -vl hdisk84', u'  hdisk84          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L168000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000450A9B5000\n\n'),
(u'lscfg -vl hdisk85', u'  hdisk85          U5802.001.0087037-P1-C2-T1-W20510002AC000A9B-L9F000000000000  3PAR InServ Virtual Volume\n\n        Manufacturer................3PARdata\n        Machine Type and Model......VV\n        Serial Number...............2AC000CE0A9B5000\n\n'),
            ])
            ssh_aix.run_ssh_aix('127.0.0.1')
        ip = IPAddress.objects.get(address='127.0.0.1')
        dev = ip.device
        self.assertNotEquals(dev, None)
        self.assertEquals(dev.model.type, DeviceType.rack_server.id)
        self.assertEquals(dev.model.name, 'IBM Power 750 Express AIX')
        macs = [e.mac for e in dev.ethernet_set.all()]
        self.assertEqual(macs, ['00215EE21898', '00215EE2189A', '00215EE21B50',
            '00215EE21B52', '00215EE22DE0', '00215EE22DE2', 'E41F134E7E8E'])
        mounts = [m.share.wwn for m in dev.disksharemount_set.all()]
        self.assertEquals(mounts, ['2AC000250A9B5000'])
        disks = [s.sn for s in dev.storage_set.all()]
        self.assertEquals(disks, ['3TB1RJQ2', '3TB1RJZS', '3TB1RKYY', '3TB1RKYZ'])
