using System;
using System.CodeDom;
using System.Management;
using System.Collections;
using System.Collections.Generic;
using DonPedro.DTO;
using DonPedro.Utils;

namespace DonPedro.Detectors
{
	public class WMIDetectorSource
	{
		protected enum SizeUnits {B, KB, MB, GB, TB};
		protected string operatingSystemVersion;
		protected string vendor;
		protected int osVersionNumber;

		public WMIDetectorSource()
		{
			operatingSystemVersion = GetOperatingSystemVersion();
			vendor = GetVendor();
			
			osVersionNumber = 6;
			try
			{
				osVersionNumber = int.Parse(
					operatingSystemVersion.Substring(0, operatingSystemVersion.IndexOf('.'))
				);
			}
			catch (Exception e)
			{
				Logger.Instance.LogError(e.ToString());
			}
		}

		public List<ProcessorDTOResponse> GetProcessorsInfo()
		{
			// Windows <= Windows Server 2003 have WMI bug. WMI reports cores as a different CPUs.
			if (osVersionNumber < 6)
			{
				return GetWinLTE6ProcessorsInfo();
			}
			
			return GetWinGTE6ProcessorsInfo();
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
					try
					{
						os.SystemMemory = ConvertSizeToMiB(Int64.Parse(obj["TotalVisibleMemorySize"].ToString()), SizeUnits.KB).ToString();
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
			os.SystemCoresCount = totalCoresCount.ToString();
			
			Int64 totalDisksSize = 0;
			foreach (StorageDTOResponse storage in GetStorageInfo())
			{
				Int64 storageSize;
				if (Int64.TryParse(storage.Size, out storageSize))
				{
					totalDisksSize += storageSize;
				}
			}
			os.SystemStorage = totalDisksSize.ToString();

			return os;
		}
		
		public List<StorageDTOResponse> GetStorageInfo()
		{
			List<StorageDTOResponse> storage = new List<StorageDTOResponse>();

			try
			{
				// In Windows <= Windows Server 2003 Win32_DiskDrive doesn't have SerialNumber field.
				string query;
				if (osVersionNumber < 6)
				{
					query = "select Caption, DeviceID, Model from Win32_DiskDrive";
				}
				else
				{
					query = "select Caption, DeviceID, SerialNumber, Model from Win32_DiskDrive";
				}
				
				SelectQuery diskDrivesQuery = new SelectQuery(query);
				ManagementObjectSearcher diskDrivesSearcher = new ManagementObjectSearcher(diskDrivesQuery);
				
				foreach (ManagementObject diskDrive in diskDrivesSearcher.Get())
				{
					string sn = "";
					if (osVersionNumber < 6)
					{
						// In Windows <= Windows Server 2003 we can find SerialNumber in Win32_PhysicalMedia.
						SelectQuery snQuery = new SelectQuery("select SerialNumber from Win32_PhysicalMedia where tag='" + GetValueAsString(diskDrive, "DeviceID").Replace(@"\", @"\\") + "'");
						ManagementObjectSearcher snSearcher = new ManagementObjectSearcher(snQuery);
						
						foreach (ManagementObject snObj in snSearcher.Get())
						{
							sn = GetValueAsString(snObj, "SerialNumber");
							break;
						}
					}
					else
					{
						sn = GetValueAsString(diskDrive, "SerialNumber");
					}
					
					if (sn.Length == 0 ||
						sn.StartsWith("QM000") ||
					    Blacklists.IsDiscVendorInBlacklist(GetValueAsString(diskDrive, "Caption").ToLower()) ||
					    Blacklists.IsDiskProductInBlacklist(GetValueAsString(diskDrive, "Model").ToLower())
					)
					{
						continue;
					}
					
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
							disk.MountPoint = GetValueAsString(diskDrive, "DeviceID");
							try
							{
								disk.Size = ConvertSizeToMiB(Int64.Parse(logicalDisk["Size"].ToString()), SizeUnits.B).ToString();
							}
							catch (Exception e)
							{
								Logger.Instance.LogError(e.ToString());
							}
							disk.SerialNumber = sn;
							
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
		
		public List<MacAddressDTOResponse> GetMacAddressInfo()
		{
			List<MacAddressDTOResponse> macAddresses = new List<MacAddressDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select MACAddress 
					  from Win32_NetworkAdapter 
					  where MACAddress<>null"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					string mac = GetValueAsString(obj, "MACAddress");
					if (Blacklists.IsMacInBlacklist(mac))
					{
						continue;
					}

					MacAddressDTOResponse macAddress = new MacAddressDTOResponse();
					macAddress.Mac = mac;

					macAddresses.Add(macAddress);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return macAddresses;
		}
		
		public List<IPAddressDTOResponse> GetIPAddressInfo()
		{
			List<IPAddressDTOResponse> ipAddresses = new List<IPAddressDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select MACAddress, Index 
					  from Win32_NetworkAdapter 
					  where MACAddress<>null"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					string mac = GetValueAsString(obj, "MACAddress");
					if (Blacklists.IsMacInBlacklist(mac))
					{
						continue;
					}
					
					try
					{
						SelectQuery queryAdapterConf = new SelectQuery(
							@"select IPAddress 
							  from Win32_NetworkAdapterConfiguration 
							  where Index='" + GetValueAsString(obj, "Index") + "' and IPEnabled=True"
						);
						ManagementObjectSearcher adapterConfSearcher = new ManagementObjectSearcher(queryAdapterConf);

						foreach (ManagementObject adapterConf in adapterConfSearcher.Get())
						{
							try
							{
								IPAddressDTOResponse ipAddress = new IPAddressDTOResponse();
								ipAddress.IPAddress = ((string[]) adapterConf["IPAddress"])[0];
								
								ipAddresses.Add(ipAddress);
							}
							catch (ManagementException e)
							{
								Logger.Instance.LogError(e.ToString());
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
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return ipAddresses;
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
					card.ModelName = card.Label;
					
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
					@"select Model, DeviceID 
					  from Win32_DiskDrive 
					  where Model like '3PARdata%'"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					SelectQuery snQuery = new SelectQuery(
						"select SerialNumber from Win32_PhysicalMedia " +
						"where tag='" + GetValueAsString(obj, "DeviceID").Replace(@"\", @"\\") + "'"
					);
					ManagementObjectSearcher snSearcher = new ManagementObjectSearcher(snQuery);
					
					foreach (ManagementObject snObj in snSearcher.Get())
					{
						DiskShareMountDTOResponse share = new DiskShareMountDTOResponse();
						share.Volume = GetValueAsString(obj, "Model");
						share.SerialNumber = GetValueAsString(snObj, "SerialNumber");
						
						mounts.Add(share);
						
						break;
					}
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return mounts;
		}
		
		public List<SoftwareDTOResponse> GetSoftwareInfo()
		{
			List<SoftwareDTOResponse> software = new List<SoftwareDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select Name, Vendor, Version 
					  from Win32_Product"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
				    SoftwareDTOResponse soft = new SoftwareDTOResponse();
				    soft.Label = GetValueAsString(obj, "Name");
				    soft.Version = GetValueAsString(obj, "Version");
				    soft.Path = GetValueAsString(obj, "Vendor") +
				    			" - " +
				    			soft.Label +
				    			" - " +
				    			GetValueAsString(obj, "Version");
				    soft.ModelName = soft.Label;
				    
				    software.Add(soft);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return software;
		}
		
		public DeviceDTOResponse GetDeviceInfo()
		{
			DeviceDTOResponse device = new DeviceDTOResponse();
			
			try
			{
				ManagementClass mc = new ManagementClass("Win32_ComputerSystemProduct");
				
				foreach (ManagementObject obj in mc.GetInstances())
				{
					device.ModelName = GetValueAsString(obj, "Vendor") + 
						               " " + 
						               GetValueAsString(obj, "Name") +
						               " " +
						               GetValueAsString(obj, "Version");
					device.SerialNumber = GetValueAsString(obj, "IdentifyingNumber");
					
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
		
		protected string GetOperatingSystemVersion()
		{
			string osVersion = "";
			
			try
			{
				SelectQuery query = new SelectQuery("select Version from Win32_OperatingSystem");
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					osVersion = GetValueAsString(obj, "Version");
					break;
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return osVersion;
		}
		
		protected string GetVendor()
		{
			string computerVendor = "";
			
			try
			{
				ManagementClass mc = new ManagementClass("Win32_ComputerSystemProduct");
				
				foreach (ManagementObject obj in mc.GetInstances())
				{
					computerVendor = GetValueAsString(obj, "Vendor");

					break;
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return computerVendor.Trim().ToLower();
		}
		
		protected List<ProcessorDTOResponse> GetWinGTE6ProcessorsInfo()
		{
			List<ProcessorDTOResponse> processors = new List<ProcessorDTOResponse>();

			try
			{
				SelectQuery query = new SelectQuery(
					@"select 
						Name, 
						DeviceID, 
						MaxClockSpeed, 
						NumberOfCores, 
						NumberOfLogicalProcessors, 
						Caption, 
						Manufacturer, 
						DataWidth
					  from Win32_Processor"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);

				foreach (ManagementObject obj in searcher.Get())
				{
					ProcessorDTOResponse processor = new ProcessorDTOResponse();
					if (vendor.IndexOf("xen") > -1 || vendor.IndexOf("vmware") > -1 || vendor.IndexOf("bochs") > -1)
					{
						processor.Label = "Virtual " + GetValueAsString(obj, "Name");
						processor.Family = "Virtual " + GetValueAsString(obj, "Caption");
					}
					else
					{
						processor.Label = GetValueAsString(obj, "Name");
						processor.Family = GetValueAsString(obj, "Caption");
					}
					processor.Speed = GetValueAsString(obj, "MaxClockSpeed");
					processor.Cores = GetValueAsString(obj, "NumberOfCores");
					processor.Index = GetValueAsString(obj, "DeviceID");
					processor.ModelName = processor.Label + " " + processor.Speed + "Mhz";
					
					processors.Add(processor);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			return processors;
		}
		
		protected List<ProcessorDTOResponse> GetWinLTE6ProcessorsInfo()
		{
			List<ProcessorDTOResponse> processors = new List<ProcessorDTOResponse>();
			Hashtable uniqueProcessors = new Hashtable();
			int totalDetectedCPUs = 0;
			
			try
			{
				SelectQuery query = new SelectQuery(
					@"select 
						Name,  
						DeviceID, 
						MaxClockSpeed, 
						Caption, 
						Manufacturer, 
						DataWidth,
						SocketDesignation
					  from Win32_Processor"
				);
				ManagementObjectSearcher searcher = new ManagementObjectSearcher(query);
				
				foreach (ManagementObject obj in searcher.Get())
				{
					totalDetectedCPUs++;
					
					string socketDesignation = GetValueAsString(obj, "SocketDesignation");
					if (uniqueProcessors.ContainsKey(socketDesignation))
					{
						continue;
					}
					
					ProcessorDTOResponse processor = new ProcessorDTOResponse();
					if (vendor.IndexOf("xen") > -1 || vendor.IndexOf("vmware") > -1 || vendor.IndexOf("bochs") > -1)
					{
						processor.Label = "Virtual " + GetValueAsString(obj, "Name");
						processor.Family = "Virtual " + GetValueAsString(obj, "Caption");
					}
					else
					{
						processor.Label = GetValueAsString(obj, "Name");
						processor.Family = GetValueAsString(obj, "Caption");
					}
					processor.Speed = GetValueAsString(obj, "MaxClockSpeed");
					processor.Index = GetValueAsString(obj, "DeviceID");
					processor.ModelName = processor.Label + " " + processor.Speed + "Mhz";
					
					uniqueProcessors.Add(socketDesignation, processor);
				}
			}
			catch (ManagementException e)
			{
				Logger.Instance.LogError(e.ToString());
			}
			
			if (uniqueProcessors.Count > 0)
			{
				int coresCount = totalDetectedCPUs / uniqueProcessors.Count;
				foreach (ProcessorDTOResponse cpu in uniqueProcessors.Values)
				{
					cpu.Cores = coresCount.ToString();
					
					processors.Add(cpu);
				}
			}
			
			return processors;
		}
	}
}
