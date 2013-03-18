data = """{"data":{"storage": [{"sn":"03da1030-f25b-47","mountpoint":"C:","size":"40957","label":"XENSRC PVDISK SCSI Disk Device"}],
 "ethernets": [{"mac":"6A:77:98:51:05:13","speed":"1000000000","label":"Citrix PV Ethernet Adapter #0","ipaddress":"10.100.0.10"}],
 "memory": [{"size":"3068","speed":"","index":"DIMM 0","sn":"","caption":"Physical Memory","label":"Physical Memory"}],
 "operating_system": {"memory":"3067","storage":"40957","corescount":"2","label":"Microsoft Windows Server 2008 R2 Standard"},
 "processors": [{"speed":"2667","cores":"1","index":"CPU0","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"},{"speed":"2667","cores":"1","index":"CPU1","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"}],
 "device": {"sn":"6ddaaa4a-dc00-de38-e683-da037fd729ca","caption":"Computer System Product","version":"4.1.2","vendor":"Xen","label":"HVM domU"},
 "fcs": [{"physicalid":"0","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"},{"physicalid":"1","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"}],
 "shares": [{"volume":"3PARdata VV  Multi-Path Disk Device","sn":"25D304C1","label":"3PARdata VV  Multi-Path Disk Device"},
  {"volume":"3PARdata VV  Multi-Path Disk Device","sn":"80C804C1","label":"3PARdata VV  Multi-Path Disk Device"}],
  "software":[{"vendor":"Vendor 1","label":"Soft 1","version":"1.2.33"}, {"vendor":"Vendor 2","label":"Soft 2","version":"0.8.99"}]
}}
"""

incomplete_data = """{"data":{"storage": [{"sn":"03da1030-f25b-47","mountpoint":"C:","size":"40957","label":"XENSRC PVDISK SCSI Disk Device"}],
 "ethernets": [],
 "memory": [{"size":"3068","speed":"","index":"DIMM 0","sn":"","caption":"Physical Memory","label":"Physical Memory"}],
 "operating_system": {"memory":"3067","storage":"40957","corescount":"8","label":"Microsoft Windows Server 2008 R2 Standard"},
 "processors": [{"speed":"2667","cores":"4","index":"CPU0","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"},{"speed":"2667","cores":"4","index":"CPU1","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"}],
 "device": {"sn":"","caption":"Computer System Product","version":"4.1.2","vendor":"Test 1","label":"HVM domU"},
 "fcs": [{"physicalid":"0","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"},{"physicalid":"1","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"}],
 "shares": [{"volume":"3PARdata VV  Multi-Path Disk Device","sn":"25D304C1","label":"3PARdata VV  Multi-Path Disk Device"},
  {"volume":"3PARdata VV  Multi-Path Disk Device","sn":"80C804C1","label":"3PARdata VV  Multi-Path Disk Device"}]
}}
"""

no_eth_data = """{"data":{"storage": [{"sn":"03da1030-f25b-48","mountpoint":"C:","size":"40957","label":"XENSRC PVDISK SCSI Disk Device"}],
 "ethernets": [],
 "memory": [{"size":"3068","speed":"","index":"DIMM 0","sn":"","caption":"Physical Memory","label":"Physical Memory"}],
 "operating_system": {"memory":"3067","storage":"40957","corescount":"8","label":"Microsoft Windows Server 2008 R2 Standard"},
 "processors": [{"speed":"2667","cores":"4","index":"CPU0","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"},{"speed":"2667","cores":"4","index":"CPU1","description":"Intel64 Family 6 Model 44 Stepping 2","numberoflogicalprocessors":"1","caption":"Intel64 Family 6 Model 44 Stepping 2","label":"Intel(R) Xeon(R) CPU           E5640  @ 2.67GHz"}],
 "device": {"sn":"7ddaaa4a-dc00-de38-e683-da037fd729ac","caption":"Computer System Product","version":"4.1.2","vendor":"Test 2","label":"HVM domU"},
 "fcs": [{"physicalid":"0","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"},{"physicalid":"1","model":"QMH2462","sn":"MY572520SK","manufacturer":"QLogic Corporation","label":"QLogic QMH2462 Fibre Channel Adapter"}],
 "shares": [{"volume":"3PARdata VV  Multi-Path Disk Device","sn":"25D304C2","label":"3PARdata VV  Multi-Path Disk Device"},
  {"volume":"3PARdata VV  Multi-Path Disk Device","sn":"80C804C2","label":"3PARdata VV  Multi-Path Disk Device"}]
}}
"""

