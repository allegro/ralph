using System;
using System.CodeDom;
using System.Management;
using System.Collections.Generic;
using DonPedro.DTO;
using DonPedro.Utils;

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

			try
			{
				SelectQuery query = new SelectQuery(
					@"select Name, Description, DeviceID, MaxClockSpeed, NumberOfCores, NumberOfLogicalProcessors, Caption
					  from Win32_Processor"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					ProcessorDTOResponse processor = new ProcessorDTOResponse();
					processor.Label = GetValueAsString(obj, "Name");
					processor.Speed = GetValueAsString(obj, "MaxClockSpeed");
					processor.Cores = GetValueAsString(obj, "NumberOfCores");
					processor.Index = GetValueAsString(obj, "DeviceID");
					processor.Description = GetValueAsString(obj, "Description");
					processor.NumberOfLogicalProcessors = GetValueAsString(obj, "NumberOfLogicalProcessors");
					processor.Caption = GetValueAsString(obj, "Caption");
					
					processors.Add(processor);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return processors;
		}
		
		public List<MemoryDTOResponse> GetMemoryInfo()
		{
			List<MemoryDTOResponse> memory = new List<MemoryDTOResponse>();
			
			try
			{
				SelectQuery query = new SelectQuery(
					@"select Name, DeviceLocator, Speed, SerialNumber, Caption, Capacity
					  from Win32_PhysicalMemory"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					MemoryDTOResponse chip = new MemoryDTOResponse();
					chip.Label = GetValueAsString(obj, "Name");
					chip.Index = GetValueAsString(obj, "DeviceLocator");
					chip.Speed = GetValueAsString(obj, "Speed");
					chip.Sn = GetValueAsString(obj, "SerialNumber");
					chip.Caption = GetValueAsString(obj, "Caption");
					try
					{
						chip.Size = ConvertSizeToMiB(
							Int64.Parse(obj["Capacity"].ToString()), 
							SizeUnits.B
						).ToString();
					}
					catch (Exception e)
					{
						Logger.Instance.LogError(e.ToString());
					}
					
					memory.Add(chip);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			if (memory.Count == 0) {
				try
				{
					SelectQuery query = new SelectQuery("select TotalPhysicalMemory, BootOptionOnLimit from Win32_ComputerSystem");
					ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
					
					foreach (ManagementObject obj in searcher.Get())
					{
						MemoryDTOResponse chip = new MemoryDTOResponse();
						chip.Label = "Virtual RAM";
						chip.Size = ConvertSizeToMiB(
							Int64.Parse(obj["TotalPhysicalMemory"].ToString()), 
							SizeUnits.B
						).ToString();
						
						memory.Add(chip);
					}
				}
				catch (ManagementException e)
				{
					Logger.Instance.LogError(e.ToString());
				}
			}
			
			return memory;
		}
		
		public OperatingSystemDTOResponse GetOperatingSystemInfo()
		{
			OperatingSystemDTOResponse os = new OperatingSystemDTOResponse();

			try
			{
				SelectQuery query = new SelectQuery("select Caption, TotalVisibleMemorySize from Win32_OperatingSystem");
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					os.Label = GetValueAsString(obj, "Caption");
					try
					{
						os.Memory = ConvertSizeToMiB(Int64.Parse(obj["TotalVisibleMemorySize"].ToString()), SizeUnits.KB).ToString();
					}
					catch (Exception e)
					{
						Logger.Instance.LogError(e.ToString());
					}
					break;
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			int totalCoresCount = 0;
			foreach (ProcessorDTOResponse cpu in GetProcessorsInfo())
			{
				int coresCount;
				if (int.TryParse(cpu.Cores, out coresCount))
				{
					totalCoresCount += coresCount;
				}
			}
			os.CoresCount = totalCoresCount.ToString();
			
			Int64 totalDisksSize = 0;
			foreach (StorageDTOResponse storage in GetStorageInfo())
			{
				Int64 storageSize;
				if (Int64.TryParse(storage.Size, out storageSize))
				{
					totalDisksSize += storageSize;
				}
			}
			os.Storage = totalDisksSize.ToString();
			
			return os;
		}
		
		public List<StorageDTOResponse> GetStorageInfo()
		{
			List<StorageDTOResponse> storage = new List<StorageDTOResponse>();

			try
			{
				SelectQuery diskDrivesQuery = new SelectQuery("select Caption, DeviceID, SerialNumber from Win32_DiskDrive");
				ManagementObjectSearcher diskDrivesSearcher = new ManagementObjectSearcher(diskDrivesQuery);
				
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
							disk.Label = GetValueAsString(diskDrive, "Caption");
							disk.MountPoint = GetValueAsString(logicalDisk, "Caption");
							try
							{
								disk.Size = ConvertSizeToMiB(Int64.Parse(logicalDisk["Size"].ToString()), SizeUnits.B).ToString();
							}
							catch (Exception e)
							{
								Logger.Instance.LogError(e.ToString());
							}
							disk.Sn = GetValueAsString(diskDrive, "SerialNumber");
							
							storage.Add(disk);
						}
					}
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return storage;
		}
		
		public List<EthernetDTOResponse> GetEthernetInfo()
		{
			List<EthernetDTOResponse> ethetnets = new List<EthernetDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select Name,  MACAddress, Speed, GUID 
					  from Win32_NetworkAdapter 
					  where MACAddress<>null and PhysicalAdapter=true"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					EthernetDTOResponse eth = new EthernetDTOResponse();
					eth.Label = GetValueAsString(obj, "Name");
					eth.Mac = GetValueAsString(obj, "MACAddress");
					eth.Speed = GetValueAsString(obj, "Speed");
					
					try
					{
						SelectQuery queryAdapterConf = new SelectQuery(
							@"select IPAddress,  IPSubnet 
							  from Win32_NetworkAdapterConfiguration 
							  where SettingID='" + GetValueAsString(obj, "GUID") + "'"
						);
						ManagementObjectSearcher adapterConfSearcher = new ManagementObjectSearcher(queryAdapterConf);

						foreach (ManagementObject adapterConf in adapterConfSearcher.Get())
						{
							try
							{
								eth.IPAddress = ((string[]) adapterConf["IPAddress"])[0];
								eth.IPSubnet = ((string[]) adapterConf["IPSubnet"])[0];
							}
							catch (ManagementException e)
							{
								Logger.Instance.LogError(e.ToString());
							}
							catch (Exception)
							{
							}
							
							break;
						}
					}
					catch (ManagementException e)
					{
						Logger.Instance.LogError(e.ToString());
					}
					
					ethetnets.Add(eth);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return ethetnets;
		}
		
		public List<FibreChannelDTOResponse> GetFibreChannelInfo()
		{
			List<FibreChannelDTOResponse> fc = new List<FibreChannelDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select Caption, DeviceID 
					  from Win32_SCSIController 
					  where Caption like '%Fibre Channel Adapter%' or Caption like '%HBA%'"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					FibreChannelDTOResponse card = new FibreChannelDTOResponse();
					card.Label = GetValueAsString(obj, "Caption");
					string[] deviveIDParts = GetValueAsString(obj, "DeviceID").Split('&');
					card.PhysicalId = deviveIDParts[deviveIDParts.Length - 1];
					
					fc.Add(card);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return fc;
		}
		
		public List<DiskShareMountDTOResponse> GetDiskShareMountInfo()
		{
			List<DiskShareMountDTOResponse> mounts = new List<DiskShareMountDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select Model, SerialNumber 
					  from Win32_DiskDrive 
					  where Model like '3PARdata%'"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					DiskShareMountDTOResponse share = new DiskShareMountDTOResponse();
					share.Volume = GetValueAsString(obj, "Model");
					share.Sn = GetValueAsString(obj, "SerialNumber");
					
					mounts.Add(share);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return mounts;
		}
		
		public DeviceDTOResponse GetDeviceInfo()
		{
			DeviceDTOResponse device = new DeviceDTOResponse();
			
			try
			{
				ManagementClass mc = new ManagementClass("Win32_ComputerSystemProduct");
				
				foreach (ManagementObject obj in mc.GetInstances())
				{
					device.Label = GetValueAsString(obj, "Name");
					device.Sn = GetValueAsString(obj, "IdentifyingNumber");
					device.Caption = GetValueAsString(obj, "Caption");
					device.Vendor = GetValueAsString(obj, "Vendor");
					device.Version = GetValueAsString(obj, "Version");
					
					break;
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return device;
		}
		
		protected string GetValueAsString(ManagementObject obj, string valueName)
		{
			try
			{
				return obj[valueName].ToString().Trim();
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
