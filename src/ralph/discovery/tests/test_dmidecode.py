#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.test import TestCase

from ralph.discovery.hardware import parse_dmidecode
from ralph.discovery.tests.samples.dmidecode_data import DATA


class DMIDecodeTest(TestCase):
    def test_parse(self):
        p = parse_dmidecode(DATA)
        self.maxDiff = None
        self.assertEqual(p['model'], 'ProLiant BL460c G6')
        self.assertEqual(p['sn'], 'GB8926V807')
        self.assertEqual(p['uuid'], '38373035-3436-4247-3839-323656383037')
        self.assertEqual(len(p['cpu']), 2)
        self.assertEqual(len(p['mem']), 4)
        self.assertEqual(p['cpu'][0], {
            '64bit': True,
            'cores': 4,
            'family': 'Quad-Core Xeon',
            'flags': [
                'CLFSH (CLFLUSH instruction supported)',
                'MCA (Machine check architecture)',
                'DE (Debugging extension)',
                'TM (Thermal monitor supported)',
                'TSC (Time stamp counter)',
                'PSE-36 (36-bit page size extension)',
                'MMX (MMX technology supported)',
                'FPU (Floating-point unit on-chip)',
                'SSE2 (Streaming SIMD extensions 2)',
                'MSR (Model specific registers)',
                'PSE (Page size extension)',
                'SS (Self-snoop)',
                'FXSR (Fast floating-point save and restore)',
                'MTRR (Memory type range registers)',
                'VME (Virtual mode extension)',
                'PBE (Pending break enabled)',
                'ACPI (ACPI supported)',
                'APIC (On-chip APIC hardware supported)',
                'SEP (Fast system call)',
                'SSE (Streaming SIMD extensions)',
                'PAT (Page attribute table)',
                'PAE (Physical address extension)',
                'CMOV (Conditional move instruction supported)',
                'PGE (Page global enable)',
                'MCE (Machine check exception)',
                'CX8 (CMPXCHG8 instruction supported)',
                'DS (Debug store)',
                'HTT (Hyper-threading technology)',
            ],
            'label': 'Proc 1',
            'model': 'Intel(R) Xeon(R) CPU E5506 @ 2.13GHz',
            'speed': 2133,
            'threads': 4,
        })
        self.assertEqual(p['mem'][0], {
            'label': u'PROC 1 DIMM 2A',
            'size': 4096,
            'speed': 1333,
            'type': u'DDR3',
        })

