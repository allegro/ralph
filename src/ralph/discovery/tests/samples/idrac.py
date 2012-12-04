nic = """<?xml version="1.0" encoding="UTF-8"?>
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
</s:Envelope>"""
