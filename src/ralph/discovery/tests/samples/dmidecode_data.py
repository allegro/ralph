#!/usr/bin/env python
# -*- coding: utf-8 -*-

DATA = '''\
# dmidecode 2.10
SMBIOS 2.6 present.
96 structures occupying 2809 bytes.
Table at 0xDF7FF000.

Handle 0x0000, DMI type 0, 24 bytes
BIOS Information
	Vendor: Hewlett-Packard
	Version: I24
	Release Date: 03/27/2009
	Address: 0xF0000
	Runtime Size: 64 kB
	ROM Size: 8192 kB
	Characteristics:
		PCI is supported
		PNP is supported
		BIOS is upgradeable
		BIOS shadowing is allowed
		ESCD support is available
		Boot from CD is supported
		Selectable boot is supported
		EDD is supported
		5.25"/360 kB floppy services are supported (int 13h)
		5.25"/1.2 MB floppy services are supported (int 13h)
		3.5"/720 kB floppy services are supported (int 13h)
		Print screen service is supported (int 5h)
		8042 keyboard services are supported (int 9h)
		Serial services are supported (int 14h)
		Printer services are supported (int 17h)
		CGA/mono video services are supported (int 10h)
		ACPI is supported
		USB legacy is supported
		BIOS boot specification is supported
		Function key-initiated network boot is supported
		Targeted content distribution is supported

Handle 0x0100, DMI type 1, 27 bytes
System Information
	Manufacturer: Hewlett-Packard
	Product Name: ProLiant BL460c G6
	Version: Not Specified
	Serial Number: GB8926V807      
	UUID: 38373035-3436-4247-3839-323656383037
	Wake-up Type: Power Switch
	SKU Number: 507864-B21      
	Family: ProLiant

Handle 0x0300, DMI type 3, 17 bytes
Chassis Information
	Manufacturer: HP
	Type: Rack Mount Chassis
	Lock: Not Present
	Version: Not Specified
	Serial Number:   GB8925V2C9 
	Asset Tag:                                 
	Boot-up State: Safe
	Power Supply State: Safe
	Thermal State: Safe
	Security Status: Unknown
	OEM Information: 0x00000000

Handle 0x0400, DMI type 4, 42 bytes
Processor Information
	Socket Designation: Proc 1
	Type: Central Processor
	Family: Quad-Core Xeon
	Manufacturer: Intel
	ID: A5 06 01 00 FF FB EB BF
	Signature: Type 0, Family 6, Model 26, Stepping 5
	Flags:
		FPU (Floating-point unit on-chip)
		VME (Virtual mode extension)
		DE (Debugging extension)
		PSE (Page size extension)
		TSC (Time stamp counter)
		MSR (Model specific registers)
		PAE (Physical address extension)
		MCE (Machine check exception)
		CX8 (CMPXCHG8 instruction supported)
		APIC (On-chip APIC hardware supported)
		SEP (Fast system call)
		MTRR (Memory type range registers)
		PGE (Page global enable)
		MCA (Machine check architecture)
		CMOV (Conditional move instruction supported)
		PAT (Page attribute table)
		PSE-36 (36-bit page size extension)
		CLFSH (CLFLUSH instruction supported)
		DS (Debug store)
		ACPI (ACPI supported)
		MMX (MMX technology supported)
		FXSR (Fast floating-point save and restore)
		SSE (Streaming SIMD extensions)
		SSE2 (Streaming SIMD extensions 2)
		SS (Self-snoop)
		HTT (Hyper-threading technology)
		TM (Thermal monitor supported)
		PBE (Pending break enabled)
	Version: Intel(R) Xeon(R) CPU E5506 @ 2.13GHz            
	Voltage: 1.4 V
	External Clock: 133 MHz
	Max Speed: 4800 MHz
	Current Speed: 2133 MHz
	Status: Populated, Enabled
	Upgrade: Socket LGA1366
	L1 Cache Handle: 0x0710
	L2 Cache Handle: 0x0720
	L3 Cache Handle: 0x0730
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Core Count: 4
	Core Enabled: 4
	Thread Count: 4
	Characteristics:
		64-bit capable

Handle 0x0406, DMI type 4, 42 bytes
Processor Information
	Socket Designation: Proc 2
	Type: Central Processor
	Family: Quad-Core Xeon
	Manufacturer: Intel
	ID: A5 06 01 00 FF FB EB BF
	Signature: Type 0, Family 6, Model 26, Stepping 5
	Flags:
		FPU (Floating-point unit on-chip)
		VME (Virtual mode extension)
		DE (Debugging extension)
		PSE (Page size extension)
		TSC (Time stamp counter)
		MSR (Model specific registers)
		PAE (Physical address extension)
		MCE (Machine check exception)
		CX8 (CMPXCHG8 instruction supported)
		APIC (On-chip APIC hardware supported)
		SEP (Fast system call)
		MTRR (Memory type range registers)
		PGE (Page global enable)
		MCA (Machine check architecture)
		CMOV (Conditional move instruction supported)
		PAT (Page attribute table)
		PSE-36 (36-bit page size extension)
		CLFSH (CLFLUSH instruction supported)
		DS (Debug store)
		ACPI (ACPI supported)
		MMX (MMX technology supported)
		FXSR (Fast floating-point save and restore)
		SSE (Streaming SIMD extensions)
		SSE2 (Streaming SIMD extensions 2)
		SS (Self-snoop)
		HTT (Hyper-threading technology)
		TM (Thermal monitor supported)
		PBE (Pending break enabled)
	Version: Intel(R) Xeon(R) CPU E5506 @ 2.13GHz            
	Voltage: 1.4 V
	External Clock: 133 MHz
	Max Speed: 4800 MHz
	Current Speed: 2133 MHz
	Status: Populated, Idle
	Upgrade: Socket LGA1366
	L1 Cache Handle: 0x0716
	L2 Cache Handle: 0x0726
	L3 Cache Handle: 0x0736
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Core Count: 4
	Core Enabled: 4
	Thread Count: 4
	Characteristics:
		64-bit capable

Handle 0x0710, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 1 Internal L1 Cache
	Configuration: Enabled, Not Socketed, Level 1
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 32 kB
	Maximum Size: 128 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Data
	Associativity: 8-way Set-associative

Handle 0x0716, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 2 Internal L1 Cache
	Configuration: Enabled, Not Socketed, Level 1
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 32 kB
	Maximum Size: 128 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Data
	Associativity: 8-way Set-associative

Handle 0x0720, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 1 Internal L2 Cache
	Configuration: Enabled, Not Socketed, Level 2
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 256 kB
	Maximum Size: 16384 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Unknown
	Associativity: 8-way Set-associative

Handle 0x0726, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 2 Internal L2 Cache
	Configuration: Enabled, Not Socketed, Level 2
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 256 kB
	Maximum Size: 16384 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Unknown
	Associativity: 8-way Set-associative

Handle 0x0730, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 1 Internal L3 Cache
	Configuration: Enabled, Not Socketed, Level 3
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 4096 kB
	Maximum Size: 8192 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Unknown
	Associativity: 16-way Set-associative

Handle 0x0736, DMI type 7, 19 bytes
Cache Information
	Socket Designation: Processor 2 Internal L3 Cache
	Configuration: Enabled, Not Socketed, Level 3
	Operational Mode: Write Back
	Location: Internal
	Installed Size: 4096 kB
	Maximum Size: 8192 kB
	Supported SRAM Types:
		Burst
	Installed SRAM Type: Burst
	Speed: Unknown
	Error Correction Type: Single-bit ECC
	System Type: Unknown
	Associativity: 16-way Set-associative

Handle 0x0801, DMI type 8, 9 bytes
Port Connector Information
	Internal Reference Designator: J53
	Internal Connector Type: Access Bus (USB)
	External Reference Designator: USB Port 1
	External Connector Type: Access Bus (USB)
	Port Type: USB

Handle 0x0802, DMI type 8, 9 bytes
Port Connector Information
	Internal Reference Designator: J53
	Internal Connector Type: Access Bus (USB)
	External Reference Designator: USB Port 2
	External Connector Type: Access Bus (USB)
	Port Type: USB

Handle 0x080D, DMI type 8, 9 bytes
Port Connector Information
	Internal Reference Designator: J3000
	Internal Connector Type: Access Bus (USB)
	External Reference Designator: USB Port 3
	External Connector Type: Access Bus (USB)
	Port Type: USB

Handle 0x0803, DMI type 8, 9 bytes
Port Connector Information
	Internal Reference Designator: J53
	Internal Connector Type: None
	External Reference Designator: Video Port
	External Connector Type: DB-15 female
	Port Type: Video Port

Handle 0x0804, DMI type 8, 9 bytes
Port Connector Information
	Internal Reference Designator: J53
	Internal Connector Type: None
	External Reference Designator: COM Port
	External Connector Type: DB-9 male
	Port Type: Serial Port 16550A Compatible

Handle 0x0901, DMI type 9, 17 bytes
System Slot Information
	Designation: Mezzanine 1
	Type: x8 PCI Express Gen 2 x8
	Current Usage: Available
	Length: Long
	Characteristics:
		3.3 V is provided
		PME signal is supported
	Bus Address: 0000:06:00.0

Handle 0x0902, DMI type 9, 17 bytes
System Slot Information
	Designation: Mezzanine 2
	Type: x8 PCI Express Gen 2 x8
	Current Usage: Available
	Length: Long
	Characteristics:
		3.3 V is provided
		PME signal is supported
	Bus Address: 0000:09:00.0

Handle 0x0903, DMI type 9, 17 bytes
System Slot Information
	Designation: Mezzanine 3
	Type: x4 PCI Express x4
	Current Usage: Available
	Length: Long
	Characteristics:
		3.3 V is provided
		PME signal is supported
	Bus Address: 0000:03:00.0

Handle 0x0B00, DMI type 11, 5 bytes
OEM Strings
	String 1: Product ID: 507864-B21      

Handle 0x1000, DMI type 16, 15 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: Single-bit ECC
	Maximum Capacity: 96 GB
	Error Information Handle: Not Provided
	Number Of Devices: 6

Handle 0x1001, DMI type 16, 15 bytes
Physical Memory Array
	Location: System Board Or Motherboard
	Use: System Memory
	Error Correction Type: Single-bit ECC
	Maximum Capacity: 96 GB
	Error Information Handle: Not Provided
	Number Of Devices: 6

Handle 0x1100, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 1
	Locator: PROC 1 DIMM 1D
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1101, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: 4096 MB
	Form Factor: DIMM
	Set: 2
	Locator: PROC 1 DIMM 2A
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: 1333 MHz
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: 2

Handle 0x1102, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 3
	Locator: PROC 1 DIMM 3E
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1103, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: 4096 MB
	Form Factor: DIMM
	Set: 4
	Locator: PROC 1 DIMM 4B
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: 1333 MHz
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: 2

Handle 0x1104, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 5
	Locator: PROC 1 DIMM 5F
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1105, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1000
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 6
	Locator: PROC 1 DIMM 6C
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1106, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 7
	Locator: PROC 2 DIMM 1D
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1107, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: 4096 MB
	Form Factor: DIMM
	Set: 8
	Locator: PROC 2 DIMM 2A
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: 1333 MHz
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: 2

Handle 0x1108, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 9
	Locator: PROC 2 DIMM 3E
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1109, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: 4096 MB
	Form Factor: DIMM
	Set: 10
	Locator: PROC 2 DIMM 4B
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: 1333 MHz
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: 2

Handle 0x110A, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 11
	Locator: PROC 2 DIMM 5F
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x110B, DMI type 17, 28 bytes
Memory Device
	Array Handle: 0x1001
	Error Information Handle: Not Provided
	Total Width: 72 bits
	Data Width: 64 bits
	Size: No Module Installed
	Form Factor: DIMM
	Set: 12
	Locator: PROC 2 DIMM 6C
	Bank Locator: Not Specified
	Type: DDR3
	Type Detail: Synchronous
	Speed: Unknown
	Manufacturer: Not Specified
	Serial Number: Not Specified
	Asset Tag: Not Specified
	Part Number: Not Specified
	Rank: Unknown

Handle 0x1300, DMI type 19, 15 bytes
Memory Array Mapped Address
	Starting Address: 0x00000000000
	Ending Address: 0x0041FFFFFFF
	Range Size: 16896 MB
	Physical Array Handle: 0x1000
	Partition Width: 0

Handle 0x1301, DMI type 19, 15 bytes
Memory Array Mapped Address
	Starting Address: 0x00000000000
	Ending Address: 0x0041FFFFFFF
	Range Size: 16896 MB
	Physical Array Handle: 0x1001
	Partition Width: 0

Handle 0x2000, DMI type 32, 11 bytes
System Boot Information
	Status: No errors detected

Handle 0x2600, DMI type 38, 18 bytes
IPMI Device Information
	Interface Type: KCS (Keyboard Control Style)
	Specification Version: 2.0
	I2C Slave Address: 0x10
	NV Storage Device: Not Present
	Base Address: 0x0000000000000CA2 (I/O)
	Register Spacing: Successive Byte Boundaries

Handle 0xC100, DMI type 193, 7 bytes
OEM-specific Type
	Header and Data:
		C1 07 00 C1 01 01 02
	Strings:
		03/27/2009
		03/11/2009

Handle 0xC101, DMI type 218, 9 bytes
OEM-specific Type
	Header and Data:
		DA 09 01 C1 00 00 00 00 00
	Strings:
		                                         

Handle 0xC200, DMI type 194, 5 bytes
OEM-specific Type
	Header and Data:
		C2 05 00 C2 01

Handle 0xC300, DMI type 195, 5 bytes
OEM-specific Type
	Header and Data:
		C3 05 00 C3 01
	Strings:
		$0E11079E

Handle 0xC400, DMI type 196, 5 bytes
OEM-specific Type
	Header and Data:
		C4 05 00 C4 00

Handle 0xC500, DMI type 197, 12 bytes
OEM-specific Type
	Header and Data:
		C5 0C 00 C5 00 04 10 01 FF 01 50 00

Handle 0xC506, DMI type 197, 12 bytes
OEM-specific Type
	Header and Data:
		C5 0C 06 C5 06 04 00 00 FF 02 50 00

Handle 0xD300, DMI type 211, 7 bytes
OEM-specific Type
	Header and Data:
		D3 07 00 D3 00 04 46

Handle 0xD306, DMI type 211, 7 bytes
OEM-specific Type
	Header and Data:
		D3 07 06 D3 06 04 46

Handle 0xC600, DMI type 198, 11 bytes
OEM-specific Type
	Header and Data:
		C6 0B 00 C6 17 00 00 01 3C 00 01

Handle 0xC700, DMI type 199, 28 bytes
OEM-specific Type
	Header and Data:
		C7 1C 00 C7 0C 00 00 00 08 20 30 10 A4 06 01 00
		0F 00 00 00 09 20 20 02 A5 06 01 00

Handle 0xCD00, DMI type 205, 22 bytes
OEM-specific Type
	Header and Data:
		CD 16 00 CD 01 01 46 41 54 78 00 00 E0 FF 00 00
		00 00 00 00 0D 00

Handle 0xCA00, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 00 CA 00 11 FF 01 01

Handle 0xCA01, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 01 CA 01 11 FF 02 01

Handle 0xCA02, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 02 CA 02 11 FF 03 01

Handle 0xCA03, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 03 CA 03 11 FF 04 01

Handle 0xCA04, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 04 CA 04 11 FF 05 01

Handle 0xCA05, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 05 CA 05 11 FF 06 01

Handle 0xCA06, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 06 CA 06 11 FF 01 02

Handle 0xCA07, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 07 CA 07 11 FF 02 02

Handle 0xCA08, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 08 CA 08 11 FF 03 02

Handle 0xCA09, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 09 CA 09 11 FF 04 02

Handle 0xCA0A, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 0A CA 0A 11 FF 05 02

Handle 0xCA0B, DMI type 202, 9 bytes
OEM-specific Type
	Header and Data:
		CA 09 0B CA 0B 11 FF 06 02

Handle 0xCC00, DMI type 204, 11 bytes
HP ProLiant System/Rack Locator
	Rack Name: Rack_208                        
	Enclosure Name: HP_Blade_208-3                  
	Enclosure Model: BladeSystem c7000 Enclosure G2                                  
	Enclosure Serial: GB8925V2C9   
	Enclosure Bays: 16
	Server Bay: 7                               
	Bays Filled: 1

Handle 0xD100, DMI type 209, 20 bytes
HP BIOS NIC PCI and MAC Information
	NIC 1: PCI device 02:00.0, MAC address 00:24:81:AE:C0:98
	NIC 2: PCI device 02:00.1, MAC address 00:24:81:AE:C0:9C

Handle 0xD200, DMI type 210, 12 bytes
OEM-specific Type
	Header and Data:
		D2 0C 00 D2 E1 00 00 00 00 00 00 00

Handle 0xD400, DMI type 212, 24 bytes
OEM-specific Type
	Header and Data:
		D4 18 00 D4 24 43 52 55 00 4C F9 FF 00 00 00 00
		00 40 00 00 00 00 00 00

Handle 0xD700, DMI type 215, 6 bytes
OEM-specific Type
	Header and Data:
		D7 06 00 D7 00 05

Handle 0xDB00, DMI type 219, 8 bytes
OEM-specific Type
	Header and Data:
		DB 08 00 DB FF 0B 00 00

Handle 0xDC00, DMI type 220, 85 bytes
OEM-specific Type
	Header and Data:
		DC 55 00 DC 10 10 00 C5 00 00 11 00 C5 00 01 12
		00 C5 01 00 13 00 C5 01 01 14 00 C5 02 00 15 00
		C5 02 01 16 00 C5 03 00 17 00 C5 03 01 00 06 C5
		00 00 01 06 C5 00 01 02 06 C5 01 00 03 06 C5 01
		01 04 06 C5 02 00 05 06 C5 02 01 06 06 C5 03 00
		07 06 C5 03 01

Handle 0xDD00, DMI type 221, 20 bytes
HP BIOS iSCSI NIC PCI and MAC Information
	NIC 1: PCI device 02:00.0, MAC address 00:24:81:AE:C0:99
	NIC 2: PCI device 02:00.1, MAC address 00:24:81:AE:C0:9D

Handle 0xDF00, DMI type 223, 7 bytes
OEM-specific Type
	Header and Data:
		DF 07 00 DF 66 46 70

Handle 0xDE00, DMI type 222, 70 bytes
OEM-specific Type
	Header and Data:
		DE 46 00 DE 01 08 F0 00 F1 00 00 00 00 00 00 00
		00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
		00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
		00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
		00 00 00 00 00 00

Handle 0xE000, DMI type 224, 5 bytes
OEM-specific Type
	Header and Data:
		E0 05 00 E0 00

Handle 0xE200, DMI type 226, 21 bytes
OEM-specific Type
	Header and Data:
		E2 15 00 E2 35 30 37 38 36 34 47 42 38 39 32 36
		56 38 30 37 01
	Strings:
		GB8926V807      

Handle 0xE300, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 00 E3 00 04 00 11 07 A2 01 00

Handle 0xE301, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 01 E3 00 04 01 11 07 A0 01 00

Handle 0xE302, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 02 E3 00 04 02 11 07 A6 01 00

Handle 0xE303, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 03 E3 00 04 03 11 07 A4 01 00

Handle 0xE304, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 04 E3 00 04 04 11 07 AA 01 00

Handle 0xE305, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 05 E3 00 04 05 11 07 A8 01 00

Handle 0xE306, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 06 E3 06 04 06 11 06 A2 01 00

Handle 0xE307, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 07 E3 06 04 07 11 06 A0 01 00

Handle 0xE308, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 08 E3 06 04 08 11 06 A6 01 00

Handle 0xE309, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 09 E3 06 04 09 11 06 A4 01 00

Handle 0xE30A, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 0A E3 06 04 0A 11 06 AA 01 00

Handle 0xE30B, DMI type 227, 12 bytes
OEM-specific Type
	Header and Data:
		E3 0C 0B E3 06 04 0B 11 06 A8 01 00

Handle 0xE400, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 00 E4 00 00 00 00 00 00 00 FF 01 00

Handle 0xE401, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 01 E4 01 00 00 00 00 00 00 FF 00 00

Handle 0xE402, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 02 E4 02 00 00 00 00 00 00 FF 00 00

Handle 0xE403, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 03 E4 03 00 00 00 00 00 00 FF 00 00

Handle 0xE404, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 04 E4 04 02 04 03 00 00 00 00 00 00

Handle 0xE405, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 05 E4 05 02 04 03 01 00 00 00 00 00

Handle 0xE406, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 06 E4 06 02 04 03 02 00 00 00 00 00

Handle 0xE407, DMI type 228, 14 bytes
OEM-specific Type
	Header and Data:
		E4 0E 07 E4 07 02 04 03 03 00 00 00 00 00

Handle 0xE408, DMI type 229, 20 bytes
OEM-specific Type
	Header and Data:
		E5 14 08 E4 24 48 44 44 00 E0 64 DF 00 00 00 00
		00 20 00 00

Handle 0x7F00, DMI type 127, 4 bytes
End Of Table'''
