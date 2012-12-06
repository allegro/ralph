base_info = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dell.com/wbem/wscim/1/cim-schema/2/DCIM_SystemView" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <s:Header>
    <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/enumeration/EnumerateResponse</wsa:Action>
    <wsa:RelatesTo>uuid:d64eb446-d017-1017-8002-9385bb730318</wsa:RelatesTo>
    <wsa:MessageID>uuid:516ba3ac-d01a-101a-8067-8a530f1cb190</wsa:MessageID>
  </s:Header>
  <s:Body>
    <wsen:EnumerateResponse>
      <wsman:Items>
        <n1:DCIM_SystemView>
          <n1:AssetTag/>
          <n1:BIOSReleaseDate>09/11/2012</n1:BIOSReleaseDate>
          <n1:BIOSVersionString>1.3.6</n1:BIOSVersionString>
          <n1:BaseBoardChassisSlot>NA</n1:BaseBoardChassisSlot>
          <n1:BatteryRollupStatus>1</n1:BatteryRollupStatus>
          <n1:BladeGeometry>4</n1:BladeGeometry>
          <n1:BoardPartNumber>0X6H47A01</n1:BoardPartNumber>
          <n1:BoardSerialNumber>CN1374029900VJ</n1:BoardSerialNumber>
          <n1:CMCIP xsi:nil="true"/>
          <n1:CPLDVersion>1.0.3</n1:CPLDVersion>
          <n1:CPURollupStatus>1</n1:CPURollupStatus>
          <n1:ChassisName>Main System Chassis</n1:ChassisName>
          <n1:ChassisServiceTag>BLSFG5J</n1:ChassisServiceTag>
          <n1:ChassisSystemHeight>2</n1:ChassisSystemHeight>
          <n1:ExpressServiceCode>25262145415</n1:ExpressServiceCode>
          <n1:FQDD>System.Embedded.1</n1:FQDD>
          <n1:FanRollupStatus>1</n1:FanRollupStatus>
          <n1:HostName/>
          <n1:InstanceID>System.Embedded.1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:LicensingRollupStatus>1</n1:LicensingRollupStatus>
          <n1:LifecycleControllerVersion>2.0.0</n1:LifecycleControllerVersion>
          <n1:Manufacturer>Dell Inc.</n1:Manufacturer>
          <n1:MaxCPUSockets>2</n1:MaxCPUSockets>
          <n1:MaxDIMMSlots>24</n1:MaxDIMMSlots>
          <n1:MaxPCIeSlots>6</n1:MaxPCIeSlots>
          <n1:MemoryOperationMode>OptimizerMode</n1:MemoryOperationMode>
          <n1:Model>PowerEdge R720xd</n1:Model>
          <n1:PSRollupStatus>3</n1:PSRollupStatus>
          <n1:PlatformGUID>4a35474f-c0c2-4680-5310-004c4c4c4544</n1:PlatformGUID>
          <n1:PopulatedCPUSockets>2</n1:PopulatedCPUSockets>
          <n1:PopulatedDIMMSlots>8</n1:PopulatedDIMMSlots>
          <n1:PopulatedPCIeSlots>2</n1:PopulatedPCIeSlots>
          <n1:PowerCap>619</n1:PowerCap>
          <n1:PowerCapEnabledState>3</n1:PowerCapEnabledState>
          <n1:PowerState>2</n1:PowerState>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:RollupStatus>1</n1:RollupStatus>
          <n1:ServerAllocation xsi:nil="true"/>
          <n1:ServiceTag>BLSFG5J</n1:ServiceTag>
          <n1:StorageRollupStatus>1</n1:StorageRollupStatus>
          <n1:SysMemErrorMethodology>6</n1:SysMemErrorMethodology>
          <n1:SysMemFailOverState>NotInUse</n1:SysMemFailOverState>
          <n1:SysMemLocation>3</n1:SysMemLocation>
          <n1:SysMemPrimaryStatus>1</n1:SysMemPrimaryStatus>
          <n1:SysMemTotalSize>65536</n1:SysMemTotalSize>
          <n1:SystemGeneration>12G Monolithic</n1:SystemGeneration>
          <n1:SystemID>1320</n1:SystemID>
          <n1:SystemRevision>0</n1:SystemRevision>
          <n1:TempRollupStatus>1</n1:TempRollupStatus>
          <n1:UUID>4c4c4544-004c-5310-8046-c2c04f47354a</n1:UUID>
          <n1:VoltRollupStatus>1</n1:VoltRollupStatus>
          <n1:smbiosGUID>44454c4c-4c00-1053-8046-c2c04f47354a</n1:smbiosGUID>
        </n1:DCIM_SystemView>
      </wsman:Items>
      <wsen:EnumerationContext/>
      <wsman:EndOfSequence/>
    </wsen:EnumerateResponse>
  </s:Body>
</s:Envelope>
"""
cpu_info = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dell.com/wbem/wscim/1/cim-schema/2/DCIM_CPUView">
  <s:Header>
    <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/enumeration/EnumerateResponse</wsa:Action>
    <wsa:RelatesTo>uuid:ea6cd545-d017-1017-8002-9385bb730318</wsa:RelatesTo>
    <wsa:MessageID>uuid:65935a16-d01a-101a-8069-8a530f1cb190</wsa:MessageID>
  </s:Header>
  <s:Body>
    <wsen:EnumerateResponse>
      <wsman:Items>
        <n1:DCIM_CPUView>
          <n1:CPUFamily>B3</n1:CPUFamily>
          <n1:CPUStatus>1</n1:CPUStatus>
          <n1:Cache1Associativity>7</n1:Cache1Associativity>
          <n1:Cache1ErrorMethodology>5</n1:Cache1ErrorMethodology>
          <n1:Cache1Level>0</n1:Cache1Level>
          <n1:Cache1PrimaryStatus>1</n1:Cache1PrimaryStatus>
          <n1:Cache1SRAMType>2</n1:Cache1SRAMType>
          <n1:Cache1Size>192</n1:Cache1Size>
          <n1:Cache1Type>4</n1:Cache1Type>
          <n1:Cache1WritePolicy>0</n1:Cache1WritePolicy>
          <n1:Cache2Associativity>7</n1:Cache2Associativity>
          <n1:Cache2ErrorMethodology>5</n1:Cache2ErrorMethodology>
          <n1:Cache2Level>1</n1:Cache2Level>
          <n1:Cache2PrimaryStatus>1</n1:Cache2PrimaryStatus>
          <n1:Cache2SRAMType>2</n1:Cache2SRAMType>
          <n1:Cache2Size>1536</n1:Cache2Size>
          <n1:Cache2Type>5</n1:Cache2Type>
          <n1:Cache2WritePolicy>0</n1:Cache2WritePolicy>
          <n1:Cache3Associativity>14</n1:Cache3Associativity>
          <n1:Cache3ErrorMethodology>5</n1:Cache3ErrorMethodology>
          <n1:Cache3Level>2</n1:Cache3Level>
          <n1:Cache3PrimaryStatus>1</n1:Cache3PrimaryStatus>
          <n1:Cache3SRAMType>2</n1:Cache3SRAMType>
          <n1:Cache3Size>15360</n1:Cache3Size>
          <n1:Cache3Type>5</n1:Cache3Type>
          <n1:Cache3WritePolicy>1</n1:Cache3WritePolicy>
          <n1:Characteristics>4</n1:Characteristics>
          <n1:CurrentClockSpeed>2500</n1:CurrentClockSpeed>
          <n1:ExternalBusClockSpeed>7200</n1:ExternalBusClockSpeed>
          <n1:FQDD>CPU.Socket.1</n1:FQDD>
          <n1:InstanceID>CPU.Socket.1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:Manufacturer>Intel</n1:Manufacturer>
          <n1:MaxClockSpeed>3600</n1:MaxClockSpeed>
          <n1:Model>Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz</n1:Model>
          <n1:NumberOfEnabledCores>6</n1:NumberOfEnabledCores>
          <n1:NumberOfEnabledThreads>12</n1:NumberOfEnabledThreads>
          <n1:NumberOfProcessorCores>6</n1:NumberOfProcessorCores>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Voltage>1.2</n1:Voltage>
        </n1:DCIM_CPUView>
        <n1:DCIM_CPUView>
          <n1:CPUFamily>B3</n1:CPUFamily>
          <n1:CPUStatus>4</n1:CPUStatus>
          <n1:Cache1Associativity>7</n1:Cache1Associativity>
          <n1:Cache1ErrorMethodology>5</n1:Cache1ErrorMethodology>
          <n1:Cache1Level>0</n1:Cache1Level>
          <n1:Cache1PrimaryStatus>1</n1:Cache1PrimaryStatus>
          <n1:Cache1SRAMType>2</n1:Cache1SRAMType>
          <n1:Cache1Size>192</n1:Cache1Size>
          <n1:Cache1Type>4</n1:Cache1Type>
          <n1:Cache1WritePolicy>0</n1:Cache1WritePolicy>
          <n1:Cache2Associativity>7</n1:Cache2Associativity>
          <n1:Cache2ErrorMethodology>5</n1:Cache2ErrorMethodology>
          <n1:Cache2Level>1</n1:Cache2Level>
          <n1:Cache2PrimaryStatus>1</n1:Cache2PrimaryStatus>
          <n1:Cache2SRAMType>2</n1:Cache2SRAMType>
          <n1:Cache2Size>1536</n1:Cache2Size>
          <n1:Cache2Type>5</n1:Cache2Type>
          <n1:Cache2WritePolicy>0</n1:Cache2WritePolicy>
          <n1:Cache3Associativity>14</n1:Cache3Associativity>
          <n1:Cache3ErrorMethodology>5</n1:Cache3ErrorMethodology>
          <n1:Cache3Level>2</n1:Cache3Level>
          <n1:Cache3PrimaryStatus>1</n1:Cache3PrimaryStatus>
          <n1:Cache3SRAMType>2</n1:Cache3SRAMType>
          <n1:Cache3Size>15360</n1:Cache3Size>
          <n1:Cache3Type>5</n1:Cache3Type>
          <n1:Cache3WritePolicy>1</n1:Cache3WritePolicy>
          <n1:Characteristics>4</n1:Characteristics>
          <n1:CurrentClockSpeed>2500</n1:CurrentClockSpeed>
          <n1:ExternalBusClockSpeed>7200</n1:ExternalBusClockSpeed>
          <n1:FQDD>CPU.Socket.2</n1:FQDD>
          <n1:InstanceID>CPU.Socket.2</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:Manufacturer>Intel</n1:Manufacturer>
          <n1:MaxClockSpeed>3600</n1:MaxClockSpeed>
          <n1:Model>Intel(R) Xeon(R) CPU E5-2640 0 @ 2.50GHz</n1:Model>
          <n1:NumberOfEnabledCores>6</n1:NumberOfEnabledCores>
          <n1:NumberOfEnabledThreads>12</n1:NumberOfEnabledThreads>
          <n1:NumberOfProcessorCores>6</n1:NumberOfProcessorCores>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Voltage>1.2</n1:Voltage>
        </n1:DCIM_CPUView>
      </wsman:Items>
      <wsen:EnumerationContext/>
      <wsman:EndOfSequence/>
    </wsen:EnumerateResponse>
  </s:Body>
</s:Envelope>
"""

memory_info = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dell.com/wbem/wscim/1/cim-schema/2/DCIM_MemoryView">
  <s:Header>
    <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/enumeration/EnumerateResponse</wsa:Action>
    <wsa:RelatesTo>uuid:ec16203c-d017-1017-8002-9385bb730318</wsa:RelatesTo>
    <wsa:MessageID>uuid:67366fa6-d01a-101a-806b-8a530f1cb190</wsa:MessageID>
  </s:Header>
  <s:Body>
    <wsen:EnumerateResponse>
      <wsman:Items>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>A</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.A1</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.A1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>3688240E</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>A</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.A2</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.A2</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>3618240D</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>A</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.A3</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.A3</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>36A82412</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>A</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.A4</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.A4</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>36882411</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>B</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.B1</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.B1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>363823F2</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>B</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.B2</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.B2</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>365823F3</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>B</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.B3</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.B3</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>36B82412</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
        <n1:DCIM_MemoryView>
          <n1:BankLabel>B</n1:BankLabel>
          <n1:CurrentOperatingSpeed>1333</n1:CurrentOperatingSpeed>
          <n1:FQDD>DIMM.Socket.B4</n1:FQDD>
          <n1:InstanceID>DIMM.Socket.B4</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129145825.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:ManufactureDate>Mon Jan 16 12:00:00 2012 UTC</n1:ManufactureDate>
          <n1:Manufacturer>Hynix Semiconductor</n1:Manufacturer>
          <n1:MemoryType>24</n1:MemoryType>
          <n1:Model>DDR3 DIMM</n1:Model>
          <n1:PartNumber>HMT31GR7BFR4A-H9</n1:PartNumber>
          <n1:PrimaryStatus>1</n1:PrimaryStatus>
          <n1:Rank>2</n1:Rank>
          <n1:SerialNumber>36482413</n1:SerialNumber>
          <n1:Size>8192</n1:Size>
          <n1:Speed>1333</n1:Speed>
        </n1:DCIM_MemoryView>
      </wsman:Items>
      <wsen:EnumerationContext/>
      <wsman:EndOfSequence/>
    </wsen:EnumerateResponse>
  </s:Body>
</s:Envelope>
"""

nic_info = """<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:wsen="http://schemas.xmlsoap.org/ws/2004/09/enumeration" xmlns:wsman="http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd" xmlns:n1="http://schemas.dell.com/wbem/wscim/1/cim-schema/2/DCIM_NICView" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <s:Header>
    <wsa:To>http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous</wsa:To>
    <wsa:Action>http://schemas.xmlsoap.org/ws/2004/09/enumeration/EnumerateResponse</wsa:Action>
    <wsa:RelatesTo>uuid:0c27001e-d00a-100a-8002-aaeb32641a00</wsa:RelatesTo>
    <wsa:MessageID>uuid:87518407-d00c-100c-802f-8a530f1cb190</wsa:MessageID>
  </s:Header>
  <s:Body>
    <wsen:EnumerateResponse>
      <wsman:Items>
        <n1:DCIM_NICView>
          <n1:AutoNegotiation>2</n1:AutoNegotiation>
          <n1:BusNumber>1</n1:BusNumber>
          <n1:ControllerBIOSVersion xsi:nil="true"/>
          <n1:CurrentMACAddress>BC:30:5B:F1:33:02</n1:CurrentMACAddress>
          <n1:DataBusWidth>0002</n1:DataBusWidth>
          <n1:DeviceNumber>0</n1:DeviceNumber>
          <n1:EFIVersion xsi:nil="true"/>
          <n1:FCoEOffloadMode>3</n1:FCoEOffloadMode>
          <n1:FCoEWWNN xsi:nil="true"/>
          <n1:FQDD>NIC.Integrated.1-3-1</n1:FQDD>
          <n1:FamilyVersion>13.5.6</n1:FamilyVersion>
          <n1:FunctionNumber>2</n1:FunctionNumber>
          <n1:InstanceID>NIC.Integrated.1-3-1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121031194539.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:LinkDuplex>0</n1:LinkDuplex>
          <n1:LinkSpeed>0</n1:LinkSpeed>
          <n1:MaxBandwidth>0</n1:MaxBandwidth>
          <n1:MediaType>1</n1:MediaType>
          <n1:MinBandwidth>0</n1:MinBandwidth>
          <n1:NicMode>3</n1:NicMode>
          <n1:PCIDeviceID>1521</n1:PCIDeviceID>
          <n1:PCISubDeviceID>1f60</n1:PCISubDeviceID>
          <n1:PCISubVendorID>1028</n1:PCISubVendorID>
          <n1:PCIVendorID>8086</n1:PCIVendorID>
          <n1:PermanentFCOEMACAddress/>
          <n1:PermanentMACAddress>BC:30:5B:F1:33:02</n1:PermanentMACAddress>
          <n1:PermanentiSCSIMACAddress/>
          <n1:ProductName>Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:02</n1:ProductName>
          <n1:ReceiveFlowControl>3</n1:ReceiveFlowControl>
          <n1:SlotLength>0002</n1:SlotLength>
          <n1:SlotType>0002</n1:SlotType>
          <n1:TransmitFlowControl>3</n1:TransmitFlowControl>
          <n1:VendorName>Intel Corp</n1:VendorName>
          <n1:VirtWWN xsi:nil="true"/>
          <n1:VirtWWPN xsi:nil="true"/>
          <n1:WWN>BC:30:5B:F1:33:02</n1:WWN>
          <n1:WWPN xsi:nil="true"/>
          <n1:iScsiOffloadMode>3</n1:iScsiOffloadMode>
        </n1:DCIM_NICView>
        <n1:DCIM_NICView>
          <n1:AutoNegotiation>2</n1:AutoNegotiation>
          <n1:BusNumber>1</n1:BusNumber>
          <n1:ControllerBIOSVersion xsi:nil="true"/>
          <n1:CurrentMACAddress>BC:30:5B:F1:33:03</n1:CurrentMACAddress>
          <n1:DataBusWidth>0002</n1:DataBusWidth>
          <n1:DeviceNumber>0</n1:DeviceNumber>
          <n1:EFIVersion xsi:nil="true"/>
          <n1:FCoEOffloadMode>3</n1:FCoEOffloadMode>
          <n1:FCoEWWNN xsi:nil="true"/>
          <n1:FQDD>NIC.Integrated.1-4-1</n1:FQDD>
          <n1:FamilyVersion>13.5.6</n1:FamilyVersion>
          <n1:FunctionNumber>3</n1:FunctionNumber>
          <n1:InstanceID>NIC.Integrated.1-4-1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121031194539.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121031155945.000000+000</n1:LastUpdateTime>
          <n1:LinkDuplex>0</n1:LinkDuplex>
          <n1:LinkSpeed>0</n1:LinkSpeed>
          <n1:MaxBandwidth>0</n1:MaxBandwidth>
          <n1:MediaType>1</n1:MediaType>
          <n1:MinBandwidth>0</n1:MinBandwidth>
          <n1:NicMode>3</n1:NicMode>
          <n1:PCIDeviceID>1521</n1:PCIDeviceID>
          <n1:PCISubDeviceID>1f60</n1:PCISubDeviceID>
          <n1:PCISubVendorID>1028</n1:PCISubVendorID>
          <n1:PCIVendorID>8086</n1:PCIVendorID>
          <n1:PermanentFCOEMACAddress/>
          <n1:PermanentMACAddress>BC:30:5B:F1:33:03</n1:PermanentMACAddress>
          <n1:PermanentiSCSIMACAddress/>
          <n1:ProductName>Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:03</n1:ProductName>
          <n1:ReceiveFlowControl>3</n1:ReceiveFlowControl>
          <n1:SlotLength>0002</n1:SlotLength>
          <n1:SlotType>0002</n1:SlotType>
          <n1:TransmitFlowControl>3</n1:TransmitFlowControl>
          <n1:VendorName>Intel Corp</n1:VendorName>
          <n1:VirtWWN xsi:nil="true"/>
          <n1:VirtWWPN xsi:nil="true"/>
          <n1:WWN>BC:30:5B:F1:33:03</n1:WWN>
          <n1:WWPN xsi:nil="true"/>
          <n1:iScsiOffloadMode>3</n1:iScsiOffloadMode>
        </n1:DCIM_NICView>
        <n1:DCIM_NICView>
          <n1:AutoNegotiation>2</n1:AutoNegotiation>
          <n1:BusNumber>1</n1:BusNumber>
          <n1:ControllerBIOSVersion xsi:nil="true"/>
          <n1:CurrentMACAddress>BC:30:5B:F1:33:00</n1:CurrentMACAddress>
          <n1:DataBusWidth>0002</n1:DataBusWidth>
          <n1:DeviceNumber>0</n1:DeviceNumber>
          <n1:EFIVersion xsi:nil="true"/>
          <n1:FCoEOffloadMode>3</n1:FCoEOffloadMode>
          <n1:FCoEWWNN xsi:nil="true"/>
          <n1:FQDD>NIC.Integrated.1-1-1</n1:FQDD>
          <n1:FamilyVersion>13.5.6</n1:FamilyVersion>
          <n1:FunctionNumber>0</n1:FunctionNumber>
          <n1:InstanceID>NIC.Integrated.1-1-1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129101647.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121129101636.000000+000</n1:LastUpdateTime>
          <n1:LinkDuplex>1</n1:LinkDuplex>
          <n1:LinkSpeed>3</n1:LinkSpeed>
          <n1:MaxBandwidth>0</n1:MaxBandwidth>
          <n1:MediaType>1</n1:MediaType>
          <n1:MinBandwidth>0</n1:MinBandwidth>
          <n1:NicMode>3</n1:NicMode>
          <n1:PCIDeviceID>1521</n1:PCIDeviceID>
          <n1:PCISubDeviceID>1f60</n1:PCISubDeviceID>
          <n1:PCISubVendorID>1028</n1:PCISubVendorID>
          <n1:PCIVendorID>8086</n1:PCIVendorID>
          <n1:PermanentFCOEMACAddress/>
          <n1:PermanentMACAddress>BC:30:5B:F1:33:00</n1:PermanentMACAddress>
          <n1:PermanentiSCSIMACAddress/>
          <n1:ProductName>Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:00</n1:ProductName>
          <n1:ReceiveFlowControl>2</n1:ReceiveFlowControl>
          <n1:SlotLength>0002</n1:SlotLength>
          <n1:SlotType>0002</n1:SlotType>
          <n1:TransmitFlowControl>3</n1:TransmitFlowControl>
          <n1:VendorName>Intel Corp</n1:VendorName>
          <n1:VirtWWN xsi:nil="true"/>
          <n1:VirtWWPN xsi:nil="true"/>
          <n1:WWN>BC:30:5B:F1:33:00</n1:WWN>
          <n1:WWPN xsi:nil="true"/>
          <n1:iScsiOffloadMode>3</n1:iScsiOffloadMode>
        </n1:DCIM_NICView>
        <n1:DCIM_NICView>
          <n1:AutoNegotiation>2</n1:AutoNegotiation>
          <n1:BusNumber>1</n1:BusNumber>
          <n1:ControllerBIOSVersion xsi:nil="true"/>
          <n1:CurrentMACAddress>BC:30:5B:F1:33:01</n1:CurrentMACAddress>
          <n1:DataBusWidth>0002</n1:DataBusWidth>
          <n1:DeviceNumber>0</n1:DeviceNumber>
          <n1:EFIVersion xsi:nil="true"/>
          <n1:FCoEOffloadMode>3</n1:FCoEOffloadMode>
          <n1:FCoEWWNN xsi:nil="true"/>
          <n1:FQDD>NIC.Integrated.1-2-1</n1:FQDD>
          <n1:FamilyVersion>13.5.6</n1:FamilyVersion>
          <n1:FunctionNumber>1</n1:FunctionNumber>
          <n1:InstanceID>NIC.Integrated.1-2-1</n1:InstanceID>
          <n1:LastSystemInventoryTime>20121129101647.000000+000</n1:LastSystemInventoryTime>
          <n1:LastUpdateTime>20121129101636.000000+000</n1:LastUpdateTime>
          <n1:LinkDuplex>1</n1:LinkDuplex>
          <n1:LinkSpeed>3</n1:LinkSpeed>
          <n1:MaxBandwidth>0</n1:MaxBandwidth>
          <n1:MediaType>1</n1:MediaType>
          <n1:MinBandwidth>0</n1:MinBandwidth>
          <n1:NicMode>3</n1:NicMode>
          <n1:PCIDeviceID>1521</n1:PCIDeviceID>
          <n1:PCISubDeviceID>1f60</n1:PCISubDeviceID>
          <n1:PCISubVendorID>1028</n1:PCISubVendorID>
          <n1:PCIVendorID>8086</n1:PCIVendorID>
          <n1:PermanentFCOEMACAddress/>
          <n1:PermanentMACAddress>BC:30:5B:F1:33:01</n1:PermanentMACAddress>
          <n1:PermanentiSCSIMACAddress/>
          <n1:ProductName>Intel(R) Gigabit 4P I350-t rNDC - BC:30:5B:F1:33:01</n1:ProductName>
          <n1:ReceiveFlowControl>2</n1:ReceiveFlowControl>
          <n1:SlotLength>0002</n1:SlotLength>
          <n1:SlotType>0002</n1:SlotType>
          <n1:TransmitFlowControl>3</n1:TransmitFlowControl>
          <n1:VendorName>Intel Corp</n1:VendorName>
          <n1:VirtWWN xsi:nil="true"/>
          <n1:VirtWWPN xsi:nil="true"/>
          <n1:WWN>BC:30:5B:F1:33:01</n1:WWN>
          <n1:WWPN xsi:nil="true"/>
          <n1:iScsiOffloadMode>3</n1:iScsiOffloadMode>
        </n1:DCIM_NICView>
      </wsman:Items>
      <wsen:EnumerationContext/>
      <wsman:EndOfSequence/>
    </wsen:EnumerateResponse>
  </s:Body>
</s:Envelope>
"""

