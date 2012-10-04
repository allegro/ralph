using System;
using DonPedro.DTO;
using DonPedro.Detectors;
using System.Collections.Generic;
using System.Management;

namespace DonPedro.Detectors
{
	public class Detector
	{
		WMIDetectorSource wmiDetector;
		
		public Detector()
		{
			wmiDetector = new WMIDetectorSource();
		}
		
		public List<ProcessorDTOResponse> GetProcessorsInfo()
		{
			return  wmiDetector.GetProcessorsInfo();
		}
		
		public List<MemoryDTOResponse> GetMemoryInfo()
		{
			return wmiDetector.GetMemoryInfo();
		}
		
		public OperatingSystemDTOResponse GetOperatingSystemInfo()
		{
			return wmiDetector.GetOperatingSystemInfo();
		}
		
		public List<StorageDTOResponse> GetStorageInfo()
		{
			return wmiDetector.GetStorageInfo();
		}
		
		public List<EthernetDTOResponse> GetEthernetInfo()
		{
			return wmiDetector.GetEthernetInfo();
		}
		
		public List<FibreChannelDTOResponse> GetFibreChannelInfo()
		{
			FCInfoDetectorSource fcinfo = new FCInfoDetectorSource();
			List<FibreChannelDTOResponse> fc = fcinfo.GetFibreChannelInfo();
			if (fc.Count == 0) {
				fc = wmiDetector.GetFibreChannelInfo();
			}
			return fc;
		}
		
		public List<DiskShareMountDTOResponse> GetDiskShareMountInfo()
		{
			return wmiDetector.GetDiskShareMountInfo();
		}
		
		public DeviceDTOResponse GetDeviceInfo()
		{
			return wmiDetector.GetDeviceInfo();
		}
		
		public string GetAllComponentsJSON()
		{
			string json = "{\"data\":{";
			json += "\"storage\": [";
			json += string.Join(",", GetStorageInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "],\n \"ethernets\": [";
			json += string.Join(",", GetEthernetInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "],\n \"fcs\": [";
			json += string.Join(",", GetFibreChannelInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "],\n \"shares\": [";
			json += string.Join(",", GetDiskShareMountInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "],\n \"operating_system\": ";
			json += GetOperatingSystemInfo().ToJSON();
			json += ",\n \"processors\": [";
			json += string.Join(",", GetProcessorsInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "],\n \"device\": ";
			json += GetDeviceInfo().ToJSON();
			json += "}}";
			return json;
		}
	}
}
