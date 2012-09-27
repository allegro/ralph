using System;
using System.Management;
using System.Collections.Generic;
using DonPedro.DTO;

namespace DonPedro.Detectors
{
	public class WMIDetectorSource
	{
		public WMIDetectorSource()
		{
		}
		
		public List<ProcessorDTOResponse> GetProcessors()
		{
			List<ProcessorDTOResponse> processors = new List<ProcessorDTOResponse>();
			SelectQuery query = new SelectQuery("select Name, Description, DeviceID, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors, Caption from Win32_Processor");
			ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
			
			try
			{
				foreach (ManagementObject obj in searcher.Get())
				{
					ProcessorDTOResponse processor = new ProcessorDTOResponse();
					processor.label = GetValueAsString(obj, "Name");
					processor.speed = GetValueAsString(obj, "MaxClockSpeed");
					processor.cores = GetValueAsString(obj, "NumberOfCores");
					processor.index = GetValueAsString(obj, "DeviceID");
					processor.description = GetValueAsString(obj, "Description");
					processor.number_of_logical_processors = GetValueAsString(obj, "NumberOfLogicalProcessors");
					processor.caption = GetValueAsString(obj, "Caption");
					
					processors.Add(processor);				
				}
			}
			catch (ManagementException e)
			{
				
			}
			
			return processors;
		}
		
		public List<MemoryDTOResponse> GetMemory()
		{
			List<MemoryDTOResponse> memory = new List<MemoryDTOResponse>();
			
			SelectQuery query = new SelectQuery("select Name, DeviceLocator, Speed, SerialNumber, Caption, Capacity from Win32_PhysicalMemory");
			ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
			
			try
			{
				foreach (ManagementObject obj in searcher.Get())
				{
					MemoryDTOResponse chip = new MemoryDTOResponse();
					chip.label = GetValueAsString(obj, "Name");
					chip.index = GetValueAsString(obj, "DeviceLocator");
					chip.speed = GetValueAsString(obj, "Speed");
					chip.sn = GetValueAsString(obj, "SerialNumber");
					chip.caption = GetValueAsString(obj, "Caption");
					chip.size = GetValueAsString(obj, "Capacity");
					
					memory.Add(chip);				
				}
			}
			catch (ManagementException e)
			{
				
			}
			
			if (memory.Count == 0) {
				try
				{
					query = new SelectQuery("select TotalPhysicalMemory, BootOptionOnLimit from Win32_ComputerSystem");
					searcher = new ManagementObjectSearcher(query);
					foreach (ManagementObject obj in searcher.Get())
					{
						MemoryDTOResponse chip = new MemoryDTOResponse();
						chip.label = "Virtual RAM";
						chip.size = GetValueAsString(obj, "TotalPhysicalMemory");
						GetValueAsString(obj, "BootOptionOnLimitfg");
						
						memory.Add(chip);
					}
				}
				catch (ManagementException e)
				{

				}
			}
			
			return memory;
		}
		
		protected string GetValueAsString(ManagementObject obj, string valueName)
		{
			try
			{
				return obj[valueName].ToString();
			}
			catch (Exception)
			{
				return "";
			}
		}
	}
}
