using System;
using System.CodeDom;
using System.Management;
using System.Collections.Generic;
using DonPedro.DTO;

namespace DonPedro.Detectors
{
	public class WMIDetectorSource
	{
		protected enum SizeUnits {B, KB, MB, GB, TB};
		
		public WMIDetectorSource()
		{
		}
		
		public List<ProcessorDTOResponse> GetProcessorsInfo()
		{
			List<ProcessorDTOResponse> processors = new List<ProcessorDTOResponse>();
			
			SelectQuery query = new SelectQuery(
				@"select Name, Description, DeviceID, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors, Caption
				  from Win32_Processor"
			);
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
			catch (ManagementException)
			{
			}
			
			return processors;
		}
		
		public List<MemoryDTOResponse> GetMemoryInfo()
		{
			List<MemoryDTOResponse> memory = new List<MemoryDTOResponse>();
			
			SelectQuery query = new SelectQuery(
				@"select Name, DeviceLocator, Speed, SerialNumber, Caption, Capacity
				  from Win32_PhysicalMemory"
			);
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
					try
					{
						chip.size = ConvertSizeToMiB(
							Int64.Parse(obj["Capacity"].ToString()), 
							SizeUnits.B
						).ToString();
					}
					catch (Exception)
					{
					}
					
					memory.Add(chip);
				}
			}
			catch (ManagementException)
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
				catch (ManagementException)
				{
				}
			}
			
			return memory;
		}
		
		public OperatingSystemDTOResponse GetOperatingSystemInfo()
		{
			OperatingSystemDTOResponse os = new OperatingSystemDTOResponse();
			
			SelectQuery query = new SelectQuery("select Caption, TotalVisibleMemorySize from Win32_OperatingSystem");
			ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
			
			try
			{
				foreach (ManagementObject obj in searcher.Get())
				{
					os.label = GetValueAsString(obj, "Caption");
					try
					{
						os.memory = ConvertSizeToMiB(Int64.Parse(obj["TotalVisibleMemorySize"].ToString()), SizeUnits.KB).ToString();
					}
					catch (Exception)
					{
					}
					break;
				}
			}
			catch (ManagementException)
			{
			}
			
			int totalCoresCount = 0;
			foreach (ProcessorDTOResponse cpu in GetProcessorsInfo())
			{
				int coresCount;
				if (int.TryParse(cpu.cores, out coresCount))
				{
					totalCoresCount += coresCount;
				}
			}
			os.coresCount = totalCoresCount.ToString();
			
			Int64 totalDisksSize = 0;
			foreach (StorageDTOResponse storage in GetStorageInfo())
			{
				Int64 storageSize;
				if (Int64.TryParse(storage.size, out storageSize))
				{
					totalDisksSize += storageSize;
				}
			}
			os.storage = totalDisksSize.ToString();
			
			return os;
		}
		
		public List<StorageDTOResponse> GetStorageInfo()
		{
			List<StorageDTOResponse> storage = new List<StorageDTOResponse>();
			
			SelectQuery diskDrivesQuery = new SelectQuery("select Caption, DeviceID, SerialNumber from Win32_DiskDrive");
			ManagementObjectSearcher diskDrivesSearcher = new ManagementObjectSearcher(diskDrivesQuery);
			
			try
			{
				foreach (ManagementObject diskDrive in diskDrivesSearcher.Get())
				{
					RelatedObjectQuery diskPartitionsQuery = new RelatedObjectQuery(
						"associators of {Win32_DiskDrive.DeviceID='" +
						GetValueAsString(diskDrive, "DeviceID") +
						"'} where AssocClass=Win32_DiskDriveToDiskPartition"
					);
					ManagementObjectSearcher diskPartitionsSearcher = new ManagementObjectSearcher(diskPartitionsQuery);
					
					foreach (ManagementObject diskPartition in diskPartitionsSearcher.Get())
					{
						RelatedObjectQuery logicalDisksQuery = new RelatedObjectQuery(
							"associators of {Win32_DiskPartition.DeviceID='" +
							GetValueAsString(diskPartition, "DeviceID") +
							"'} where AssocClass=Win32_LogicalDiskToPartition"
						);
						ManagementObjectSearcher logicalDisksSearcher = new ManagementObjectSearcher(logicalDisksQuery);
						
						foreach (ManagementObject logicalDisk in logicalDisksSearcher.Get())
						{
							StorageDTOResponse disk = new StorageDTOResponse();
							disk.label = GetValueAsString(diskDrive, "Caption");
							disk.mountPoint = GetValueAsString(logicalDisk, "Caption");
							disk.size = GetValueAsString(logicalDisk, "Size");
							try
							{
								disk.size = ConvertSizeToMiB(Int64.Parse(logicalDisk["Size"].ToString()), SizeUnits.B).ToString();
							}
							catch (Exception)
							{
							}
							disk.sn = GetValueAsString(diskDrive, "SerialNumber");
							
							storage.Add(disk);
						}
					}
				}
			}
			catch (ManagementException)
			{
			}
			
			return storage;
		}
		
		public List<EthernetDTOResponse> GetEthernetInfo()
		{
			List<EthernetDTOResponse> ethetnets = new List<EthernetDTOResponse>();
			
			SelectQuery query = new SelectQuery(
				@"select Name,  MACAddress, Speed 
				  from Win32_NetworkAdapter 
				  where MACAddress<>null and PhysicalAdapter=true"
			);
			ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
			
			try
			{
				foreach (ManagementObject obj in searcher.Get())
				{
					EthernetDTOResponse eth = new EthernetDTOResponse();
					eth.label = GetValueAsString(obj, "Name");
					eth.mac = GetValueAsString(obj, "MACAddress");
					eth.speed = GetValueAsString(obj, "Speed");
					
					ethetnets.Add(eth);
				}
			}
			catch (ManagementException)
			{
			}
			
			return ethetnets;
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
		
		protected Int64 ConvertSizeToMiB(Int64 size, SizeUnits inputUnit)
		{
			switch (inputUnit)
			{
				case SizeUnits.B:
					return (Int64) Math.Ceiling((double) (size / 1024 / 1024));
				case SizeUnits.KB:
					return (Int64) Math.Ceiling((double) (size / 1024));
				case SizeUnits.GB:
					return size * 1024;
				case SizeUnits.TB:
					return size * 1024 * 1024;
			}
			
			return size;
		}
	}
}
