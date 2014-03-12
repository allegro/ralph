# -*- coding: utf-8 -*-

JUNIPER_SHOW_VERSION_SAMPLE = """
fpc0:
--------------------------------------------------------------------------
Hostname: rack01-sw1.dc
Model: ex4500-40f
...

fpc1:
--------------------------------------------------------------------------
Hostname: rack01-sw1.dc4
Model: ex4500-40f
...
"""

JUNIPER_STACKED_SAMPLE = """
Preprovisioned Virtual Chassis
Virtual Chassis ID: aaaa.bbbb.cccc
Virtual Chassis Mode: Enabled
                                           Mstr           Mixed Neighbor List
Member ID  Status   Serial No    Model     prio  Role      Mode ID  Interface
0 (FPC 0)  Prsnt    GX1122334401 ex4500-40f 129  Backup       N  1  vcp-1
                                                                 1  vcp-0
1 (FPC 1)  Prsnt    GX1122334402 ex4500-40f 129  Master*      N  0  vcp-1
                                                                 0  vcp-0

{master:1}
"""

JUNIPER_NOT_STACKED_SAMPLE = """
Virtual Chassis ID: aaaa.bbbb.dddd
Virtual Chassis Mode: Enabled
                                           Mstr           Mixed Neighbor List
Member ID  Status   Serial No    Model     prio  Role      Mode ID  Interface
0 (FPC 0)  Prsnt    GX1122334403 ex4500-40f 128  Master*      N

Member ID for next new member: 1 (FPC 1)

{master:0}
"""

JUNIPER_GET_MAC_ADDRESSES_SAMPLE = """
    FPC 0   MAC address information:
      Public base address     aa:bb:cc:dd:00:01
      Public count            64
    FPC 1   MAC address information:
      Public base address     aa:bb:cc:dd:00:02
      Public count            64
"""
