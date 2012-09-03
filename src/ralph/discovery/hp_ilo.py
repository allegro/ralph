#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import ssl as sslmod
import socket
import urllib
import threading
import xml.etree.ElementTree as elementtree


# Taken from dmidecode.c version 2.11
CPU_FAMILY = {
    0x01: "Other",
    0x02: "Unknown",
    0x03: "8086",
    0x04: "80286",
    0x05: "80386",
    0x06: "80486",
    0x07: "8087",
    0x08: "80287",
    0x09: "80387",
    0x0A: "80487",
    0x0B: "Pentium",
    0x0C: "Pentium Pro",
    0x0D: "Pentium II",
    0x0E: "Pentium MMX",
    0x0F: "Celeron",
    0x10: "Pentium II Xeon",
    0x11: "Pentium III",
    0x12: "M1",
    0x13: "M2",
    0x14: "Celeron M",
    0x15: "Pentium 4 HT",

    0x18: "Duron",
    0x19: "K5",
    0x1A: "K6",
    0x1B: "K6-2",
    0x1C: "K6-3",
    0x1D: "Athlon",
    0x1E: "AMD29000",
    0x1F: "K6-2+",
    0x20: "Power PC",
    0x21: "Power PC 601",
    0x22: "Power PC 603",
    0x23: "Power PC 603+",
    0x24: "Power PC 604",
    0x25: "Power PC 620",
    0x26: "Power PC x704",
    0x27: "Power PC 750",
    0x28: "Core Duo",
    0x29: "Core Duo Mobile",
    0x2A: "Core Solo Mobile",
    0x2B: "Atom",

    0x30: "Alpha",
    0x31: "Alpha 21064",
    0x32: "Alpha 21066",
    0x33: "Alpha 21164",
    0x34: "Alpha 21164PC",
    0x35: "Alpha 21164a",
    0x36: "Alpha 21264",
    0x37: "Alpha 21364",
    0x38: "Turion II Ultra Dual-Core Mobile M",
    0x39: "Turion II Dual-Core Mobile M",
    0x3A: "Athlon II Dual-Core M",
    0x3B: "Opteron 6100",
    0x3C: "Opteron 4100",

    0x40: "MIPS",
    0x41: "MIPS R4000",
    0x42: "MIPS R4200",
    0x43: "MIPS R4400",
    0x44: "MIPS R4600",
    0x45: "MIPS R10000",

    0x50: "SPARC",
    0x51: "SuperSPARC",
    0x52: "MicroSPARC II",
    0x53: "MicroSPARC IIep",
    0x54: "UltraSPARC",
    0x55: "UltraSPARC II",
    0x56: "UltraSPARC IIi",
    0x57: "UltraSPARC III",
    0x58: "UltraSPARC IIIi",

    0x60: "68040",
    0x61: "68xxx",
    0x62: "68000",
    0x63: "68010",
    0x64: "68020",
    0x65: "68030",

    0x70: "Hobbit",

    0x78: "Crusoe TM5000",
    0x79: "Crusoe TM3000",
    0x7A: "Efficeon TM8000",

    0x80: "Weitek",

    0x82: "Itanium",
    0x83: "Athlon 64",
    0x84: "Opteron",
    0x85: "Sempron",
    0x86: "Turion 64",
    0x87: "Dual-Core Opteron",
    0x88: "Athlon 64 X2",
    0x89: "Turion 64 X2",
    0x8A: "Quad-Core Opteron",
    0x8B: "Third-Generation Opteron",
    0x8C: "Phenom FX",
    0x8D: "Phenom X4",
    0x8E: "Phenom X2",
    0x8F: "Athlon X2",
    0x90: "PA-RISC",
    0x91: "PA-RISC 8500",
    0x92: "PA-RISC 8000",
    0x93: "PA-RISC 7300LC",
    0x94: "PA-RISC 7200",
    0x95: "PA-RISC 7100LC",
    0x96: "PA-RISC 7100",

    0xA0: "V30",
    0xA1: "Quad-Core Xeon 3200",
    0xA2: "Dual-Core Xeon 3000",
    0xA3: "Quad-Core Xeon 5300",
    0xA4: "Dual-Core Xeon 5100",
    0xA5: "Dual-Core Xeon 5000",
    0xA6: "Dual-Core Xeon LV",
    0xA7: "Dual-Core Xeon ULV",
    0xA8: "Dual-Core Xeon 7100",
    0xA9: "Quad-Core Xeon 5400",
    0xAA: "Quad-Core Xeon",
    0xAB: "Dual-Core Xeon 5200",
    0xAC: "Dual-Core Xeon 7200",
    0xAD: "Quad-Core Xeon 7300",
    0xAE: "Quad-Core Xeon 7400",
    0xAF: "Multi-Core Xeon 7400",
    0xB0: "Pentium III Xeon",
    0xB1: "Pentium III Speedstep",
    0xB2: "Pentium 4",
    0xB3: "Xeon",
    0xB4: "AS400",
    0xB5: "Xeon MP",
    0xB6: "Athlon XP",
    0xB7: "Athlon MP",
    0xB8: "Itanium 2",
    0xB9: "Pentium M",
    0xBA: "Celeron D",
    0xBB: "Pentium D",
    0xBC: "Pentium EE",
    0xBD: "Core Solo",
    0xBF: "Core 2 Duo",
    0xC0: "Core 2 Solo",
    0xC1: "Core 2 Extreme",
    0xC2: "Core 2 Quad",
    0xC3: "Core 2 Extreme Mobile",
    0xC4: "Core 2 Duo Mobile",
    0xC5: "Core 2 Solo Mobile",
    0xC6: "Core i7",
    0xC7: "Dual-Core Celeron",
    0xC8: "IBM390",
    0xC9: "G4",
    0xCA: "G5",
    0xCB: "ESA/390 G6",
    0xCC: "z/Architectur",
    0xCD: "Core i5",
    0xCE: "Core i3",

    0xD2: "C7-M",
    0xD3: "C7-D",
    0xD4: "C7",
    0xD5: "Eden",
    0xD6: "Multi-Core Xeon",
    0xD7: "Dual-Core Xeon 3xxx",
    0xD8: "Quad-Core Xeon 3xxx",
    0xD9: "Nano",
    0xDA: "Dual-Core Xeon 5xxx",
    0xDB: "Quad-Core Xeon 5xxx",

    0xDD: "Dual-Core Xeon 7xxx",
    0xDE: "Quad-Core Xeon 7xxx",
    0xDF: "Multi-Core Xeon 7xxx",
    0xE0: "Multi-Core Xeon 3400",

    0xE6: "Embedded Opteron Quad-Core",
    0xE7: "Phenom Triple-Core",
    0xE8: "Turion Ultra Dual-Core Mobile",
    0xE9: "Turion Dual-Core Mobile",
    0xEA: "Athlon Dual-Core",
    0xEB: "Sempron SI",
    0xEC: "Phenom II",
    0xED: "Athlon II",
    0xEE: "Six-Core Opteron",
    0xEF: "Sempron M",

    0xFA: "i860",
    0xFB: "i960",

    0x104: "SH-3",
    0x105: "SH-4",
    0x118: "ARM",
    0x119: "StrongARM",
    0x12C: "6x86",
    0x12D: "MediaGX",
    0x12E: "MII",
    0x140: "WinChip",
    0x15E: "DSP",
    0x1F4: "Video Processor",
}


class Error(Exception):
    pass

class ResponseError(Error):
    pass

class VersionError(Error):
    pass


class IloHost(object):
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.version = None
        self.name = None
        self.mac = None
        self.firmware = None
        self.records = {}

    def update(self, raw=None):
        tree, raw = self._get_tree(raw)
        self.raw = raw
        (self.name, self.mac, self.firmware,
                self.records) = self._parse_tree(tree)
        fields = self.records[1][0]
        self.model = fields['Product Name'][0].strip()
        if not self.model.startswith('HP '):
            self.model = 'HP ' + self.model
        self.sn = fields['Serial Number'][0].strip()
        if self.sn in ('DC2', 'DC3', ''):
            self.sn = None

    def _get_ilo3(self, xml):
        url = 'https://%s:443/ribcl' % self.host
        try:
            f = urllib.urlopen(url, xml)
        except socket.error as e:
            raise ResponseError(str(e))
        def closer():
            try:
                f.close()
            except:
                pass
        threading.Timer(17, closer).start()
        try:
            return f.read()
        except AttributeError:
            raise ResponseError('timeout.')
        finally:
            try:
                f.close()
            except:
                pass

    def _get_ilo2(self, xml):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        try:
            sock.connect((self.host, 443))
        except socket.error as e:
            raise ResponseError(str(e))
        data = []
        try:
            def closer():
                try:
                    sock.close()
                except:
                    pass
            threading.Timer(17, closer).start()
            try:
                ssl = socket.ssl(sock)
            except (socket.error, sslmod.SSLError) as e:
                raise ResponseError(str(e))
            try:
                for line in xml.split('\n'):
                    ssl.write(line + '\r\n')
                ssl.write('\r\n')
                chunk = ssl.read()
            except socket.error as e:
                raise ResponseError(str(e))
            if chunk.startswith('HTTP'):
                message = chunk.splitlines()[0].split(None, 1)[1]
                code = message.split(None, 1)[0]
                error = ResponseError(message)
                error.code = int(code)
                raise error
            try:
                while chunk:
                    data.append(chunk)
                    chunk = ssl.read()
            except socket.error as e:
                raise ResponseError(str(e))
        finally:
            try:
                sock.close()
            except:
                pass
        return ''.join(data)

    def _get_ilo_version(self):
        try:
            self._get_ilo2('<?xml version="1.0"?><RIBCL VERSION="2.0"></RIBCL>')
        except ResponseError as e:
            if hasattr(e, 'code'):
                if e.code == 405:
                    return 3
                if e.code == 501:
                    return 1
            raise
        return 2

    def _get_ilo(self, xml):
        if self.version is None:
            self.version = self._get_ilo_version()
        if self.version == 1:
            raise VersionError('Version 1 of ilo not supported.')
        elif self.version == 2:
            return self._get_ilo2(xml)
        return self._get_ilo3(xml)

    def _get_tree(self, raw=None):
        if raw is None:
            query = """<?xml version="1.0"?>
    <RIBCL VERSION="2.0">
        <LOGIN USER_LOGIN="%s" PASSWORD="%s">
            <RIB_INFO MODE="read">
                <GET_NETWORK_SETTINGS/>
                <GET_FW_VERSION/>
            </RIB_INFO>
            <SERVER_INFO MODE="read">
                <GET_HOST_DATA/>
            </SERVER_INFO>
        </LOGIN>
    </RIBCL>""" % (self.user, self.password)
            raw = self._get_ilo(query)
        response = ('<?xml version="1.0"?><ROOT>%s</ROOT>' %
                    raw.replace('<?xml version="1.0"?>', ''))

        # XXX ILO2 sometimes gives you malformed xml...
        response = response.replace('<RIBCL VERSION="2.22"/>',
                                    '<RIBCL VERSION="2.22">')
        try:
            tree = elementtree.XML(response)
        except elementtree.ParseError:
            raise ResponseError('Invalid XML in response.')
        return tree, raw

    def _parse_tree(self, tree):
        fw_node = tree.find('RIBCL/GET_FW_VERSION')
        if fw_node is not None:
            fw = fw_node.attrib
            firmware = '%s, %s, rev %s' % (fw.get('LICENSE_TYPE', ''),
                                      fw['FIRMWARE_DATE'],
                                      fw['FIRMWARE_VERSION'])
        else:
            firmware = None

        net = tree.find('RIBCL/GET_NETWORK_SETTINGS')
        if net is None:
            raise ResponseError('No network settings in response.')
        mac = net.find('MAC_ADDRESS').attrib['VALUE'].replace(':', '').upper()
        name = net.find('DNS_NAME').attrib['VALUE'].strip()


        host = tree.find('RIBCL/GET_HOST_DATA')
        records = collections.defaultdict(list)
        for record in host.iterfind('SMBIOS_RECORD'):
            fields = collections.defaultdict(list)
            for field in record.iterfind('FIELD'):
                fields[field.attrib['NAME']].append(field.attrib['VALUE'])
            #fields['DATA'] = base64.b64decode(record.attrib['B64_DATA'])
            records[int(record.attrib['TYPE'])].append(fields)

        return name, mac, firmware, records

    @property
    def memories(self):
        for fields in self.records[17]:
            try:
                size = int(fields['Size'][0].split(None, 1)[0])
            except (ValueError, IndexError):
                continue
            try:
                speed = int(fields['Speed'][0].split(None, 1)[0])
            except (ValueError, IndexError):
                speed = None
            yield fields['Label'][0], size, speed

    @property
    def ethernets(self):
        for did in (209, 221):
            for fields in self.records[did]:
                for port, mac in zip(fields['Port'], fields['MAC']):
                    mac_addr = mac.replace('-', '').upper()
                    label = '%s, Port %s' % (fields.get('Subject', [did])[0],
                                             port)
                    yield label, mac_addr

    @property
    def cpus(self):
        for fields in self.records[4]:
            try:
                speed = int(fields['Speed'][0].split(None, 1)[0])
            except (ValueError, IndexError):
                continue
            try:
                cores = int(fields['Execution Technology'][0].split(None, 1)[0])
            except (ValueError, IndexError):
                cores = None
            extra = '\n'.join([
                ''.join(fields.get("Execution Technology", [])),
                ''.join(fields.get("Memory Technology", [])),
            ])
            family = int(''.join(fields.get("Family", [])) or 0)
            yield fields['Label'][0], speed, cores, extra, CPU_FAMILY.get(family)

    def _raw_to_tree(self, raw):
        xml = ('<?xml version="1.0"?><ROOT>%s</ROOT>' %
               raw.replace('<?xml version="1.0"?>', ''))
        xml = xml.replace('<RIBCL VERSION="2.22"/>', '<RIBCL VERSION="2.22">')
        try:
            tree = elementtree.XML(xml)
        except elementtree.ParseError:
            raise ResponseError('Invalid XML in response.')
        return tree

    def is_server_power_on(self):
        query = """<?xml version="1.0"?>
    <RIBCL VERSION="2.0">
        <LOGIN USER_LOGIN="%s" PASSWORD="%s">
            <SERVER_INFO MODE="read">
                <GET_HOST_POWER_STATUS/>
            </SERVER_INFO>
        </LOGIN>
    </RIBCL>""" % (self.user, self.password)
        tree = self._raw_to_tree(self._get_ilo(query))
        node = tree.find('RIBCL/GET_HOST_POWER')
        if node is None:
            raise ResponseError('Could not detect server power state.')
        state = node.attrib.get('HOST_POWER')
        return state == 'ON'

    def power_on(self):
        query = """<?xml version="1.0"?>
    <RIBCL VERSION="2.0">
        <LOGIN USER_LOGIN="%s" PASSWORD="%s">
            <SERVER_INFO MODE="write">
                <SET_HOST_POWER HOST_POWER="No"/>
            </SERVER_INFO>
        </LOGIN>
    </RIBCL>""" % (self.user, self.password)
        tree = self._raw_to_tree(self._get_ilo(query))
        node = tree.find('RIBCL/RESPONSE')
        if node is None:
            raise ResponseError('Invalid XML in response.')
        status = node.attrib.get('STATUS')
        return int(status, 0) == 0

    def reboot(self, power_on_if_disabled=False):
        query = """<?xml version="1.0"?>
    <RIBCL VERSION="2.0">
        <LOGIN USER_LOGIN="%s" PASSWORD="%s">
            <SERVER_INFO MODE="write">
                <RESET_SERVER/>
            </SERVER_INFO>
        </LOGIN>
    </RIBCL>""" % (self.user, self.password)
        tree = self._raw_to_tree(self._get_ilo(query))
        node = tree.find('RIBCL/RESPONSE')
        if node is None:
            raise ResponseError('Invalid XML in response.')
        status = node.attrib.get('STATUS')
        if int(status, 0) == 0:
            return True
        msg = node.attrib.get('MESSAGE')
        if 'powered off' in msg and power_on_if_disabled:
            return self.power_on()
        return False
