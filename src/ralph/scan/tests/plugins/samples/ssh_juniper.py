# -*- coding: utf-8 -*-

JUNIPER_SAMPLE = """
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
