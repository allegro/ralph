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
		
		public string GetAllComponentsJSON()
		{
			List<BaseDTOResponse> components = GetAllComponents();
			string[] jsonParts = new string[components.Count];
			
			int i = 0;
			foreach (BaseDTOResponse component in components)
			{
				jsonParts[i] = component.ToJSON();
				i++;
			}
			
			return "{" + string.Join(",", jsonParts) + "}";
		}
	}
}
