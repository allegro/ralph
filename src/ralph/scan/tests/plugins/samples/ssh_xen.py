# -*- coding: utf-8 -*-

TEST_SUDO_MODE_SAMPLE = """
uuid ( RO)          : sample-uuid-02
    name-label ( RW): test-xen-002
       address ( RO): 10.10.10.02

...
"""

GET_CURRENT_HOST_UUID_SAMPLE = """
uuid ( RO)          : sample-uuid-02
    name-label ( RW): test-xen-002
       address ( RO): 10.10.10.02


uuid ( RO)          : sample-uuid-01
    name-label ( RW): test-xen-001
       address ( RO): 10.10.10.01

"""

GET_RUNNING_VMS_SAMPLE = """
uuid ( RO)             : vm-sample-uuid-1
       name-label ( RW): app-1
      power-state ( RO): running
    memory-actual ( RO): 4294938624
     VCPUs-number ( RO): 2


uuid ( RO)             : vm-sample-uuid-2
       name-label ( RW): app-2
      power-state ( RO): running
    memory-actual ( RO): 17179840512
     VCPUs-number ( RO): 8


uuid ( RO)             : vm-sample-uuid-3
       name-label ( RW): app-3
      power-state ( RO): running
    memory-actual ( RO): 2147454976
     VCPUs-number ( RO): 2


uuid ( RO)             : vm-sample-uuid-4
       name-label ( RW): app-4
      power-state ( RO): running
    memory-actual ( RO): 8589905920
     VCPUs-number ( RO): 4


uuid ( RO)             : vm-sample-uuid-5
       name-label ( RW): app-5
      power-state ( RO): running
    memory-actual ( RO): 2147483648
     VCPUs-number ( RO): 2


uuid ( RO)             : vm-sample-uuid-6
       name-label ( RW): app-6
      power-state ( RO): running
    memory-actual ( RO): 2147454976
     VCPUs-number ( RO): 2
"""

GET_MACS_SAMPLE = """
vm-name-label ( RO)    : app-1
              MAC ( RO): 11:22:33:44:55:01


vm-name-label ( RO)    : app-1
              MAC ( RO): 11:22:33:44:55:02


vm-name-label ( RO)    : app-2
              MAC ( RO): 11:22:33:44:55:03


vm-name-label ( RO)    : app-3
              MAC ( RO): 11:22:33:44:55:04


vm-name-label ( RO)    : app-4
              MAC ( RO): 11:22:33:44:55:05
cl

vm-name-label ( RO)    : app-5
              MAC ( RO): 11:22:33:44:55:06


vm-name-label ( RO)    : app-6
              MAC ( RO): 11:22:33:44:55:07


vm-name-label ( RO)    : app-7
              MAC ( RO): 11:22:33:44:55:08


"""

GET_DISKS_SAMPLE = """
Disk 0 VBD:
vm-name-label ( RO)    : app-1
           device ( RO): hda
             type ( RW): Disk


Disk 0 VDI:
uuid ( RO)            : uuid-1
         sr-uuid ( RO): uuid-2
    virtual-size ( RO): 25769803776


Disk 0 VBD:
vm-name-label ( RO)    : app-4
           device ( RO): hda
             type ( RW): Disk


Disk 0 VDI:
uuid ( RO)            : uuid-3
         sr-uuid ( RO): uuid-4
    virtual-size ( RO): 53687091200


Disk 0 VBD:
vm-name-label ( RO)    : app-1
           device ( RO): hda
             type ( RW): Disk


Disk 0 VDI:
uuid ( RO)            : uuid-5
         sr-uuid ( RO): uuid-6
    virtual-size ( RO): 25769803776
"""
