# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.plugins import ilo_hp
from ralph.discovery.models import DeviceType


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
        self.assertEqual(
            macs, ['00215AAFA3D8', '00215AAFC712', '00215AAFC713'])

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
        self.assertEqual(models, [
            'CPU Unknown 2500MHz, 4-core',
            'CPU Unknown 2500MHz, 4-core'
        ])
