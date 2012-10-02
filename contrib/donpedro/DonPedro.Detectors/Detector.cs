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
		
		public string getAllComponentsJSON()
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
			json += "],\n \"operating_system\": [";
			json += GetOperatingSystemInfo().ToJSON();
			json += "],\n \"processors\": [";
			json += string.Join(",", GetProcessorsInfo().ConvertAll(s => s.ToJSON()).ToArray());
			json += "]}}";
			return json;
		}
		
		public List<BaseDTOResponse> GetAllComponents()
		{
			List<BaseDTOResponse> components = new List<BaseDTOResponse>();
			
			foreach (ProcessorDTOResponse obj in GetProcessorsInfo())
			{
				components.Add(obj);
			}
			
			foreach (MemoryDTOResponse obj in GetMemoryInfo())
			{
				components.Add(obj);
			}
			
			foreach (StorageDTOResponse storage in GetStorageInfo())
			{
				components.Add(storage);
			}
			
			foreach (EthernetDTOResponse eth in GetEthernetInfo())
			{
				components.Add(eth);
			}
			
			foreach (FibreChannelDTOResponse fc in GetFibreChannelInfo())
			{
				components.Add(fc);
			}
			
			foreach (DiskShareMountDTOResponse share in GetDiskShareMountInfo())
			{
				components.Add(share);
			}
			
			components.Add(GetOperatingSystemInfo());

			return components;
		}
	}
}
