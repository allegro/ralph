# -*- coding: utf-8 -*-

NODE_SN = "        Serial Number: XYZ1234567890"

NODE_MAC = "eth0      Link encap:Ethernet  HWaddr 20:20:20:20:20:20"

DEVICE_INFO_SAMPLE = """
{
   "cpu" : 0,
   "cpuinfo" : {
      "cpus" : 32,
      "hvm" : 1,
      "mhz" : "1999.986",
      "model" : "Intel(R) Xeon(R) CPU F7-666 0 @ 2.00GHz",
      "sockets" : 2,
      "user_hz" : 100
   },
   "idle" : 0,
   "kversion" : "Linux 2.6.32-16-pve #1 SMP Fri Nov 1 11:11:11 CET 2011",
   "loadavg" : [
      "1.00",
      "1.00",
      "1.00"
   ],
   "memory" : {
      "free" : 35881873408,
      "total" : 67513417728,
      "used" : 31631544320
   },
   "pveversion" : "pve-manager/2.2-31/eaae11e1",
   "rootfs" : {
      "avail" : 174798942208,
      "free" : 170328330240,
      "total" : 188863287296,
      "used" : 4470611968
   },
   "swap" : {
      "free" : 8138252288,
      "total" : 8138252288,
      "used" : 0
   },
   "uptime" : 58786946,
   "wait" : 0
}
"""

VM_INFO_SAMPLE = """
{
   "bootdisk" : "virtio0",
   "cores" : 1,
   "digest" : "aaa1b5111112ccc5e35a3375205a20480aaabbbc",
   "ide2" : "none,media=cdrom",
   "memory" : 1024,
   "name" : "test_node.local",
   "net0" : "virtio=10:10:10:10:10:10,bridge=vmbr0",
   "onboot" : 1,
   "ostype" : "l26",
   "sockets" : 1,
   "virtio0" : "vg00:vm-0123456-disk-1,size=8G"
}
"""
