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
				
			return components;
		}
	}
}
