# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.plugins import ipmi
from ralph.discovery.models import DeviceType, Device



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


